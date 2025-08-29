# Material Scraper for Donizo

A web scraper for extracting product information from Castorama.fr

## How to Run the Scraper

### Prerequisites

-   Python 3.13 or higher
-   uv package manager

### Installation

1. Clone the repository:

```bash
git clone https://github.com/SrijanDas/pricing-engine.git
cd material-scraper
```

2. Install dependencies:

```bash
uv install
```

### Running the Scraper

Execute the main script:

```bash
uv run main.py
```

The scraper will automatically:

-   Use Selenium WebDriver to handle JavaScript content
-   Scrape all configured product categories
-   Save results to `products_selenium.json`
-   Display a summary of scraped products

### Configuration

Edit `src/config.py` to modify the categories to scrape:

```python
categories = [
    'tiles',
    'evier',
    'toilettes',
    'paint',
    'meuble vasque',
    'showers'
]
```

## Output Format Description

The scraper generates JSON files with the following structure:

```json
{
    "scrape_timestamp": "2025-08-29 22:51:17",
    "total_products": 391,
    "scraper_type": "selenium",
    "products": [
        {
            "name": "Product Name",
            "category": "tiles",
            "price": 31.44,
            "currency": "EUR",
            "product_url": "https://www.castorama.fr/...",
            "brand": "Brand Name or Seller Info",
            "unit": "m²",
            "image_url": "https://media.castorama.fr/..."
        }
    ]
}
```

### Field Descriptions

-   `name`: Full product title as displayed on the website
-   `category`: Search term used to find the product
-   `price`: Numerical price value (float)
-   `currency`: Always "EUR" for Euro currency
-   `product_url`: Direct link to the product page
-   `brand`: Brand name or seller information (may be empty)
-   `unit`: Measurement unit (m², pièce, L, kg, kit, etc.)
-   `image_url`: URL to product thumbnail image

## Data Assumptions and Transformations

### Price Processing

-   Prices are extracted using regex pattern `(\d+[,.]?\d*)`
-   Non-numeric price text is filtered out
-   Products without valid prices are excluded

### Unit Extraction

-   Units are extracted from product descriptions using pattern matching
-   Common units: m², m2, pièce, unité, L, kg, kit, lot
-   Empty unit field if no unit information is found

### Category Mapping

-   Products are tagged with the search term used to find them
-   French search terms are used: "evier", "toilettes", "meuble vasque"
-   Multiple products may appear in multiple categories

### Brand Information

-   Extracted from seller information when available
-   May include "Vendu et expédié par" (Sold and shipped by) prefix
-   Empty string if no brand/seller data is found

## Handling of Pagination and Anti-Bot Logic

### Pagination Strategy

-   Automatically processes multiple pages per category (up to 3 pages max)
-   Page navigation through URL parameters: `?term=category&page=N`
-   Stops pagination when no products are found on a page

### Anti-Bot Detection Measures

The scraper implements comprehensive anti-bot detection measures:

-   Runs Chrome in headless mode with anti-detection options
-   Disables automation flags and webdriver properties
-   Human-like scrolling simulation
-   Realistic window size (1920x1080)
-   Extended delays between category switches (15-30 seconds)

#### Error Handling

-   Automatic retry mechanism (up to 3 attempts per page)
-   Detection of anti-bot pages (Cloudflare, CAPTCHA)
-   Graceful handling of timeout and connection errors
-   Proper WebDriver cleanup on exit

#### Rate Limiting

-   Maximum 3 pages per category for performance
-   Built-in delays prevent overwhelming the server
-   Random delays between requests to mimic human behavior
