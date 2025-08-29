import requests
from bs4 import BeautifulSoup
import json
import time
import re
import random
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional


class CastoramaScraper:
    def __init__(self):
        self.base_url = "https://www.castorama.fr"
        self.session = requests.Session()

        # Rotate User Agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]

        self._setup_session()

        self.search_terms = [
            'carrelage',  # tiles in French
            'evier',      # sinks in French
            'toilettes',  # toilets in French
            'peinture',   # paint in French
            'meuble vasque',  # vanities in French
            'douche'      # showers in French
        ]

        # Add delays between requests
        self.min_delay = 2
        self.max_delay = 5

    def _setup_session(self):
        """Setup session with realistic headers"""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Cache-Control': 'max-age=0'
        })

    def _random_delay(self):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def _get_homepage_first(self):
        """Visit homepage first to establish session like a real user"""
        try:
            print("Visiting homepage first...")
            response = self.session.get(self.base_url, timeout=15)
            if response.status_code == 200:
                print("Homepage visit successful")
                self._random_delay()
                return True
        except Exception as e:
            print(f"Homepage visit failed: {e}")
        return False

    def get_page_content(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        for attempt in range(retries):
            try:
                # Rotate user agent occasionally
                if attempt > 0:
                    self._setup_session()
                    print(f"Retry {attempt + 1} with new user agent")

                # Add referer for subsequent requests
                if 'search' in url:
                    self.session.headers.update({'Referer': self.base_url})

                response = self.session.get(url, timeout=20)

                # Check for common anti-bot responses
                if response.status_code == 403:
                    print(
                        f"403 Forbidden - likely blocked. Attempt {attempt + 1}")
                    if attempt < retries - 1:
                        time.sleep(random.uniform(10, 20))  # Longer wait
                        continue
                    return None

                if response.status_code == 429:
                    print(f"429 Rate Limited. Waiting before retry...")
                    time.sleep(random.uniform(30, 60))
                    continue

                response.raise_for_status()

                # Debug: Print response info
                print(f"Response status: {response.status_code}")
                print(
                    f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
                print(f"Response size: {len(response.content)} bytes")

                # Check if response is actually HTML
                content_type = response.headers.get('content-type', '').lower()
                if 'html' not in content_type:
                    print(f"Warning: Expected HTML but got {content_type}")
                    if attempt < retries - 1:
                        self._random_delay()
                        continue
                    return None

                # Try to detect encoding issues or anti-bot pages
                try:
                    soup = BeautifulSoup(response.content, 'html')

                    # Check for common anti-bot indicators
                    title = soup.find('title')
                    title_text = title.text.lower() if title else ""

                    # Check for Cloudflare, captcha, or bot detection pages
                    anti_bot_indicators = [
                        'checking your browser',
                        'cloudflare',
                        'captcha',
                        'bot detection',
                        'access denied',
                        'blocked',
                        'security check'
                    ]

                    if any(indicator in title_text for indicator in anti_bot_indicators):
                        print(f"Anti-bot page detected: {title_text}")
                        if attempt < retries - 1:
                            print("Waiting longer before retry...")
                            time.sleep(random.uniform(20, 40))
                            continue
                        return None

                    # Check for garbled content
                    page_text = soup.get_text()[:500]
                    if any(char in page_text for char in ['Ž', 'äo', 'MûÓ']) or len(page_text.strip()) < 100:
                        print("Detected garbled content")
                        if attempt < retries - 1:
                            self._random_delay()
                            continue

                        # Try different decoding as last resort
                        for encoding in ['utf-8', 'iso-8859-1', 'cp1252']:
                            try:
                                decoded = response.content.decode(encoding)
                                if 'html' in decoded.lower()[:200] and len(decoded.strip()) > 100:
                                    print(
                                        f"Successfully decoded with {encoding}")
                                    return BeautifulSoup(decoded, 'lxml')
                            except UnicodeDecodeError:
                                continue

                        print("Could not properly decode response")
                        return None

                    print(f"Page title: {title_text}")
                    return soup

                except Exception as e:
                    print(f"Error parsing HTML: {e}")
                    if attempt < retries - 1:
                        self._random_delay()
                        continue
                    return None

            except requests.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    wait_time = random.uniform(5, 15) * (attempt + 1)
                    print(f"Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                    continue

        print(f"Failed to get content after {retries} attempts")
        return None

    def extract_price(self, price_text: str) -> Optional[float]:
        if not price_text:
            return None
        price_match = re.search(r'(\d+[,.]?\d*)', price_text.replace(' ', ''))
        if price_match:
            return float(price_match.group(1).replace(',', '.'))
        return None

    def scrape_product_list(self, category: str, max_products: int = 30) -> List[Dict]:
        products = []
        page = 1

        # Visit homepage first to establish session
        if not hasattr(self, '_homepage_visited'):
            self._get_homepage_first()
            self._homepage_visited = True

        while len(products) < max_products:
            url = f"{self.base_url}/search?term={category}&page={page}"

            print(f"Scraping {category} page {page}: {url}")

            soup = self.get_page_content(url)
            if not soup:
                print(f"Failed to get content for {category} page {page}")
                break

            # Debug: Print just the title and check for products
            title = soup.find('title')
            print(f"Page title: {title.text if title else 'No title'}")

            # Look for various product container patterns
            product_selectors = [
                {'tag': 'div', 'attrs': {'data-testid': 'product'}},
                {'tag': 'article', 'attrs': {
                    'class': re.compile(r'product', re.I)}},
                {'tag': 'div', 'attrs': {'class': re.compile(
                    r'product.*card|item.*product', re.I)}},
                {'tag': 'div', 'attrs': {'class': re.compile(
                    r'tile.*product|product.*tile', re.I)}},
                {'tag': 'li', 'attrs': {
                    'class': re.compile(r'product', re.I)}},
            ]

            product_containers = []
            for selector in product_selectors:
                containers = soup.find_all(selector['tag'], selector['attrs'])
                if containers:
                    print(
                        f"Found {len(containers)} products using selector: {selector}")
                    product_containers = containers
                    break

            if not product_containers:
                print(f"No products found on page {page} for {category}")
                # Print some debug info about page structure
                print("Available div classes (first 10):")
                divs = soup.find_all('div', class_=True)[:10]
                for div in divs:
                    classes = div.get('class', [])
                    print(f"  {' '.join(classes)}")
                break

            page_products = 0
            for container in product_containers:
                if len(products) >= max_products:
                    break

                product = self.extract_product_data(container, category)
                if product:
                    products.append(product)
                    page_products += 1

            print(f"Extracted {page_products} products from page {page}")

            if page_products == 0:
                break

            page += 1
            self._random_delay()  # Random delay between pages

            if page > 10:  # Safety limit
                break

        return products

    def extract_product_data(self, container, category_name: str) -> Optional[Dict]:
        try:
            # Look for product name with data-testid first
            name_elem = container.find('p', {'data-testid': 'product-name'})
            if not name_elem:
                # Fallback to other methods
                name_elem = container.find(
                    ['h3', 'h2', 'h4', 'span', 'a'], class_=re.compile(r'title|name|product', re.I))
            if not name_elem:
                name_elem = container.find('a')

            if not name_elem or not name_elem.get_text(strip=True):
                return None

            # Clean up the name by removing nested font tags
            name = name_elem.get_text(strip=True)

            # Look for price with data-testid first
            price_elem = container.find(
                'span', {'data-testid': 'product-price'})
            if not price_elem:
                # Look in primary-price container
                primary_price = container.find(
                    'span', {'data-testid': 'primary-price'})
                if primary_price:
                    price_elem = primary_price.find(
                        'span', {'data-testid': 'product-price'})

            if not price_elem:
                # Fallback to class-based search
                price_elem = container.find(
                    ['span', 'div'], class_=re.compile(r'price', re.I))
            if not price_elem:
                price_elem = container.find(text=re.compile(r'€'))
                if price_elem:
                    price_elem = price_elem.parent

            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self.extract_price(price_text)

            if not price:
                return None

            # Look for product URL
            url_elem = container.find('a', {'data-testid': 'product-link'})
            if not url_elem:
                url_elem = name_elem if name_elem and name_elem.name == 'a' else container.find(
                    'a')

            product_url = ""
            if url_elem and url_elem.get('href'):
                product_url = urljoin(self.base_url, url_elem['href'])

            # Look for brand/seller info - this might not be in the basic product card
            brand_elem = container.find('p', {'data-testid': 'seller-info'})
            if not brand_elem:
                brand_elem = container.find(
                    ['span', 'div', 'p'], class_=re.compile(r'brand|marque|seller', re.I))
            brand = brand_elem.get_text(strip=True) if brand_elem else ""

            # Look for image
            img_elem = container.find('img', {'data-testid': 'product-image'})
            if not img_elem:
                img_elem = container.find('img')

            image_url = ""
            if img_elem:
                if img_elem.get('src'):
                    image_url = urljoin(self.base_url, img_elem['src'])
                elif img_elem.get('data-src'):
                    image_url = urljoin(self.base_url, img_elem['data-src'])
                # Also check srcset for higher quality images
                elif img_elem.get('srcset'):
                    srcset = img_elem.get('srcset')
                    # Extract the first URL from srcset
                    first_url = srcset.split(',')[0].split(' ')[0]
                    if first_url:
                        image_url = urljoin(self.base_url, first_url)

            # Look for unit information in the product text
            unit_elem = container.find(text=re.compile(
                r'(m²|m2|pièce|unité|l|kg|kit|lot)', re.I))
            unit = ""
            if unit_elem:
                unit_match = re.search(
                    r'(m²|m2|pièce|unité|l|kg|kit|lot)', unit_elem, re.I)
                if unit_match:
                    unit = unit_match.group(1)

            # If no unit found, try to extract from product name
            if not unit:
                unit_match = re.search(r'(kit|lot|pack|set)', name.lower())
                if unit_match:
                    unit = unit_match.group(1)

            return {
                "name": name,
                "category": category_name,
                "price": price,
                "currency": "EUR",
                "product_url": product_url,
                "brand": brand,
                "unit": unit,
                "image_url": image_url
            }

        except Exception as e:
            print(f"Error extracting product data: {e}")
            return None

    def scrape_all_categories(self) -> List[Dict]:
        all_products = []
        products_per_category = 100

        for category in self.search_terms:
            print(f"\nScraping category: {category}")
            products = self.scrape_product_list(
                category, products_per_category)
            all_products.extend(products)
            print(f"Found {len(products)} products in {category}")

            # Longer delay between categories to avoid being blocked
            # Don't sleep after last category
            if category != self.search_terms[-1]:
                delay = random.uniform(10, 20)
                print(
                    f"Sleeping for {delay:.1f} seconds before next category...")
                time.sleep(delay)

        return all_products

    def scrape_search_terms(self) -> List[Dict]:
        """Scrape using search terms instead of category URLs"""
        all_products = []
        products_per_term = 100 // len(self.search_terms)

        for category_name, search_term in self.search_terms.items():
            print(f"\nSearching for: {category_name} (term: {search_term})")
            search_url = f"/search?term={search_term}"
            products = self.scrape_product_list(
                search_url, category_name, products_per_term)
            all_products.extend(products)
            print(f"Found {len(products)} products for {category_name}")
            time.sleep(2)

        return all_products

    def scrape_single_search(self, search_term: str, max_products: int = 30) -> List[Dict]:
        """Scrape a single search term"""
        search_url = f"/search?term={search_term}"
        return self.scrape_product_list(search_url, search_term.capitalize(), max_products)

    def save_to_json(self, products: List[Dict], filename: str = "castorama_products.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "scrape_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_products": len(products),
                "products": products
            }, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(products)} products to {filename}")
