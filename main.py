from src.scraper import CastoramaScraper
from src.selenium_scraper import CastoramaSeleniumScraper


def run_requests_scraper():
    """Try scraping with requests first"""
    print("Starting Castorama scraper using requests...")
    scraper = CastoramaScraper()
    products = scraper.scrape_all_categories()

    if products:
        scraper.save_to_json(products, "products.json")
        return products
    return []


def run_selenium_scraper():
    """Fallback to Selenium if requests fails"""
    try:
        print("Starting Castorama scraper using Selenium...")
        scraper = CastoramaSeleniumScraper(headless=True)
        products = scraper.scrape_all_categories()
        scraper.close()

        if products:
            scraper.save_to_json(products, "products_selenium.json")
            return products
    except ImportError:
        print("Selenium not available. Install with: pip install selenium")
        print("Also need to install ChromeDriver")
    except Exception as e:
        print(f"Selenium scraping failed: {e}")

    return []


def main():
    print("Material Scraper for Donizo")
    print("=" * 50)

    products = run_selenium_scraper()

    if products:
        categories = {}
        for product in products:
            cat = product['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        print("\nProducts by category:")
        for cat, count in categories.items():
            print(f"  {cat}: {count} products")

        print(f"\nSample products:")
        for i, product in enumerate(products[:3]):
            print(f"\n{i+1}. {product['name']}")
            print(f"   Category: {product['category']}")
            print(f"   Price: {product['price']} {product['currency']}")
            print(f"   Brand: {product['brand'] or 'N/A'}")
            print(f"   Unit: {product['unit'] or 'N/A'}")

    else:
        print("No products were successfully scraped")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
