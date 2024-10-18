## ProductScrape/main.py

import asyncio
import aiofiles
import os
from src.product import ProductInfoScraper
from src.review import ReviewScraper
from src.utils import log_info, track_progress_during_scraping

# Helper function to count product files
def count_scraped_product_files():
    products_folder = "data/Products"
    product_count = 0
    if os.path.exists(products_folder):
        # Count all product.json files in the Products folder
        for root, dirs, files in os.walk(products_folder):
            product_count += len([f for f in files if f == 'product.json'])
    return product_count

# Helper function to count review files
def count_scraped_review_files():
    products_folder = "data/Products"
    review_count = 0
    if os.path.exists(products_folder):
        # Count all review files (review_*.json) in the Products folder
        for root, dirs, files in os.walk(products_folder):
            review_count += len([f for f in files if f.startswith('review_') and f.endswith('.json')])
    return review_count

async def get_store_urls():
    choice = input("Do you want to use the store list from 'stores.txt'? (y/n): ").strip().lower()
    if choice == 'y':
        return await load_store_urls_from_file()
    else:
        custom_url = input("Enter the Shopify store URL: ").strip()
        return [custom_url]

async def load_store_urls_from_file():
    filepath = "data/stores.txt"
    try:
        async with aiofiles.open(filepath, "r", encoding="utf-8") as file:
            return [line.strip() for line in await file.readlines() if line.strip()]
    except FileNotFoundError:
        log_info("No 'stores.txt' file found.")
        return []

async def scrape_store_data(store_url, products_scraped, reviews_scraped):
    log_info(f"Starting to scrape {store_url}")
    product_scraper = ProductInfoScraper(store_url)
    await product_scraper.initialize()  # Load previously scraped products

    # Start scraping collections
    await product_scraper.scrape_all_collections()

    # Count product files and update the products_scraped count
    products_scraped[0] = count_scraped_product_files()
    log_info(f"Total products scraped so far: {products_scraped[0]}")

async def scrape_reviews_for_products(product_data, store_url, reviews_scraped):
    log_info(f"Scraping reviews for products in {store_url}...")
    review_scraper = ReviewScraper(product_data, store_url)
    review_scraper.scrape_reviews()

    # Count review files and update the reviews_scraped count
    reviews_scraped[0] = count_scraped_review_files()
    log_info(f"Total reviews scraped so far: {reviews_scraped[0]}")

async def process_store(store_url, products_scraped, reviews_scraped):
    product_data = await scrape_store_data(store_url, products_scraped, reviews_scraped)
    if product_data:
        await scrape_reviews_for_products(product_data, store_url, reviews_scraped)

async def main():
    store_urls = await get_store_urls()

    # Variables to track the counts of scraped products and reviews
    products_scraped = [0]  # List so it's mutable
    reviews_scraped = [0]   # List so it's mutable

    # Track progress during scraping
    await track_progress_during_scraping(
        asyncio.gather(*(process_store(store_url, products_scraped, reviews_scraped) for store_url in store_urls)),
        products_scraped,
        reviews_scraped
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScraping interrupted. Exiting...")
