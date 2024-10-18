## ProductScrape/src/product.py

import aiohttp
import asyncio
from aiohttp import ClientConnectorError
from src.utils import save_product_data, log_info, log_debug, is_duplicate, load_scraped_products, save_scraped_products
from src.parser import HTMLParser

class ProductInfoScraper:
    def __init__(self, store_url):
        self.store_url = store_url
        self.product_data = []
        self.scraped_products = {}  # Initialize scraped_products to an empty dict
        self.parser = HTMLParser()  # Initialize the HTML parser

    async def initialize(self):
        self.scraped_products = await load_scraped_products()  # Load previously scraped products

    async def get_collections(self):
        collections_url = f"{self.store_url}/collections.json"
        collection_handles = []
        page = 1

        while True:
            paginated_url = f"{collections_url}?page={page}&limit=250"
            async with aiohttp.ClientSession() as session:
                async with session.get(paginated_url) as response:
                    if response.status == 200:
                        collections = await response.json()
                        new_collections = collections.get('collections', [])
                        if not new_collections:
                            break  # Exit loop if no more collections are returned
                        for collection in new_collections:
                            collection_handles.append(collection['handle'])
                        log_info(f"Found {len(new_collections)} collections on page {page} in {self.store_url}")
                    else:
                        log_info(f"Failed to retrieve collections from {self.store_url}, page {page}")
                        log_debug(f"Failed with status code: {response.status}")
                        break
            page += 1

        log_info(f"Total collections found: {len(collection_handles)} in {self.store_url}")
        return collection_handles

    async def scrape_collection_products(self, collection_handle):
        page = 1
        while True:
            collection_url = f"{self.store_url}/collections/{collection_handle}/products.json?page={page}"
            async with aiohttp.ClientSession() as session:
                async with session.get(collection_url) as response:
                    if response.status == 200:
                        products = await response.json()
                        if not products.get("products"):
                            break  # Exit pagination if no more products
                        for product in products.get("products", []):
                            product_handle = product.get("handle")
                            if not is_duplicate(product_handle, self.scraped_products):  # Avoid duplicates
                                formatted_product = self.format_product_data(product)
                                additional_product_data = await self.fetch_reviews_json(product_handle)
                                if additional_product_data:
                                    formatted_product.update(additional_product_data)
                                # Save product data
                                self.product_data.append(formatted_product)
                                await save_product_data(formatted_product, product_handle)  
                                self.scraped_products[product_handle] = formatted_product["title"]
                                await save_scraped_products(self.scraped_products)  # Save after each product
                        log_info(f"Scraped page {page} of collection '{collection_handle}'")
                    else:
                        log_info(f"Failed to scrape products from collection '{collection_handle}', page {page}")
                        break
            page += 1

    async def scrape_all_collections(self):
        await self.initialize()  # Load previously scraped products before scraping
        collections = await self.get_collections()
        for collection_handle in collections:
            await self.scrape_collection_products(collection_handle)
        if not collections:
            await self.scrape_products_from_main()
        await save_scraped_products(self.scraped_products)

    async def scrape_products_from_main(self):
        products_url = f"{self.store_url}/products.json"
        page = 1
        while True:
            paginated_url = f"{products_url}?page={page}"
            async with aiohttp.ClientSession() as session:
                async with session.get(paginated_url) as response:
                    if response.status == 200:
                        products = await response.json()
                        if not products.get("products"):
                            break
                        for product in products.get("products", []):
                            product_handle = product.get("handle")
                            if not is_duplicate(product_handle, self.scraped_products):
                                formatted_product = self.format_product_data(product)
                                additional_product_data = await self.fetch_reviews_json(product_handle)
                                if additional_product_data:
                                    formatted_product.update(additional_product_data)
                                self.product_data.append(formatted_product)
                                await save_product_data(formatted_product, product_handle)
                                self.scraped_products[product_handle] = formatted_product["title"]
                                await save_scraped_products(self.scraped_products)
                        log_info(f"Scraped page {page} from main {self.store_url}/products.json")
                    else:
                        log_info(f"Failed to scrape main product page {page} from {self.store_url}")
                        break
            page += 1

    async def fetch_reviews_json(self, product_handle):
        reviews_url = f"{self.store_url}/products/{product_handle}/reviews.json"
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(reviews_url) as response:
                        if response.status == 200:
                            additional_data = await response.json()
                            if additional_data and "product" in additional_data:
                                return {
                                    "variants": additional_data["product"]["variants"],
                                    "weight": additional_data["product"]["variants"][0].get("weight"),
                                    "inventory_quantity": additional_data["product"]["variants"][0].get("inventory_quantity"),
                                    "compare_at_price": additional_data["product"]["variants"][0].get("compare_at_price"),
                                    "images": [
                                        {
                                            "src": self.parser.parse_html_to_text(image.get("src")),  # Clean image URL
                                            "alt": self.parser.parse_html_to_text(image.get("alt")),  # Clean alt text
                                            "width": image.get("width"),
                                            "height": image.get("height")
                                        } for image in additional_data["product"].get("images", [])
                                    ]
                                }
                        log_info(f"Failed to retrieve additional product data from {reviews_url}")
            except ClientConnectorError as e:
                log_info(f"Connection error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1} of {max_retries})")
                await asyncio.sleep(retry_delay)
            except Exception as e:
                log_info(f"An error occurred: {e}")
        
        log_info(f"Failed to retrieve data from {reviews_url} after {max_retries} attempts")
        return None

    def format_product_data(self, product):
        description_html = product.get("body_html", "")
        cleaned_description = self.parser.parse_html_to_text(description_html)  # Clean HTML description

        cleaned_title = self.parser.parse_html_to_text(product.get("title", ""))  # Clean product title
        cleaned_vendor = self.parser.parse_html_to_text(product.get("vendor", ""))  # Clean vendor
        cleaned_product_type = self.parser.parse_html_to_text(product.get("product_type", ""))  # Clean product type

        return {
            "title": cleaned_title,
            "handle": product.get("handle"),
            "vendor": cleaned_vendor,
            "product_type": cleaned_product_type,
            "tags": [self.parser.parse_html_to_text(tag) for tag in product.get("tags", [])],  # Clean tags
            "price": self.get_variant_price(product),
            "description": cleaned_description,  # Use cleaned description
            "created_at": product.get("created_at"),
            "updated_at": product.get("updated_at"),
            "variants": product.get("variants", []),
            "images": [
                {
                    "src": image,
                } for image in product.get("images", [])
            ]
        }

    def get_variant_price(self, product):
        variants = product.get("variants", [])
        if variants:
            return variants[0].get("price")
        return None
