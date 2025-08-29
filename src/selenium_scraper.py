"""
Alternative scraper using Selenium WebDriver for JavaScript-heavy sites
"""
import time
import random
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import json
from bs4 import BeautifulSoup
from . import CastoramaScraper


class CastoramaSeleniumScraper:
    def __init__(self, headless: bool = True):
        self.base_url = "https://www.castorama.fr"
        self.headless = headless
        self.driver = None

        self.search_terms = [
            'carrelage',  # tiles in French
            'evier',      # sinks in French
            'toilettes',  # toilets in French
            'peinture',   # paint in French
            'meuble vasque',  # vanities in French
            'douche'      # showers in French
        ]

    def _setup_driver(self):
        """Setup Chrome WebDriver with anti-detection options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Anti-detection options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Speed up loading
        chrome_options.add_argument("--disable-javascript")  # If JS not needed

        # Realistic window size
        chrome_options.add_argument("--window-size=1920,1080")

        # User agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)

            # Execute script to remove webdriver property
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("Chrome WebDriver setup successful")
            return True
        except Exception as e:
            print(f"Failed to setup Chrome WebDriver: {e}")
            print("Make sure ChromeDriver is installed and in PATH")
            return False

    def _random_delay(self, min_delay: float = 2, max_delay: float = 5):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def _human_like_scroll(self):
        """Simulate human-like scrolling"""
        # Scroll down gradually
        total_height = self.driver.execute_script(
            "return document.body.scrollHeight")
        current_position = 0
        scroll_increment = random.randint(300, 600)

        while current_position < total_height:
            self.driver.execute_script(
                f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.5))
            current_position += scroll_increment

            # Update total height in case page loaded more content
            total_height = self.driver.execute_script(
                "return document.body.scrollHeight")

    def scrape_search_page(self, search_term: str, max_pages: int = 3) -> List[Dict]:
        """Scrape products from search results"""
        if not self.driver:
            if not self._setup_driver():
                return []

        products = []

        try:
            # Visit homepage first
            print("Visiting homepage...")
            self.driver.get(self.base_url)
            self._random_delay(3, 7)

            # Perform search
            search_url = f"{self.base_url}/search?term={search_term}"
            print(f"Searching for: {search_term}")
            self.driver.get(search_url)
            self._random_delay(3, 5)

            scraper = CastoramaScraper()

            for page in range(1, max_pages + 1):
                print(f"Scraping page {page}")

                # Wait for page to load
                try:
                    soup = BeautifulSoup(
                        self.driver.page_source, 'html.parser')
                    if not soup:
                        print(
                            f"Failed to get content for {search_term} page {page}")
                        break

                    product_containers = soup.find_all(
                        attrs={"data-testid": "product"})

                    print(
                        f"Found {len(product_containers)} products on page {page}")

                    # Process each product container
                    for container in product_containers:
                        product = scraper.extract_product_data(
                            container, search_term)
                        if product:
                            products.append(product)

                    print(
                        f"Extracted {len([p for p in products if p])} products from page {page}")

                    # Check if we should continue to next page
                    if len(product_containers) == 0:
                        print("No more products found, stopping pagination")
                        break

                    # Navigate to next page if not the last page
                    if page < max_pages:
                        next_page_url = f"{search_url}&page={page + 1}"
                        print(f"Navigating to page {page + 1}")
                        self.driver.get(next_page_url)
                        self._random_delay(3, 5)

                except TimeoutException:
                    print(f"Page {page} load timeout")
                    break

        except Exception as e:
            print(f"Error scraping search page: {e}")

        return products

    def scrape_all_categories(self) -> List[Dict]:
        """Scrape all categories"""
        all_products = []

        for category in self.search_terms:
            print(f"\nScraping category: {category}")
            products = self.scrape_search_page(category, max_pages=3)
            all_products.extend(products)
            print(f"Found {len(products)} products in {category}")

            # Longer delay between categories
            if category != self.search_terms[-1]:
                delay = random.uniform(15, 30)
                print(f"Waiting {delay:.1f} seconds before next category...")
                time.sleep(delay)

        return all_products

    def save_to_json(self, products: List[Dict], filename: str = "castorama_products_selenium.json"):
        """Save products to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "scrape_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_products": len(products),
                "scraper_type": "selenium",
                "products": products
            }, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(products)} products to {filename}")

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
