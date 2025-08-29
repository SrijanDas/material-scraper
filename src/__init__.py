from .scraper import CastoramaScraper

try:
    from .selenium_scraper import CastoramaSeleniumScraper
    __all__ = ['CastoramaScraper', 'CastoramaSeleniumScraper']
except ImportError:
    __all__ = ['CastoramaScraper']
