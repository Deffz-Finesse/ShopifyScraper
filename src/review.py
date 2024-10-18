## ProductScrape/src/review.py

import requests
from src.utils import save_review_data, log_info, log_debug
from src.parser import HTMLParser  # Import the parser

class ReviewScraper:
    def __init__(self, product_data, store_url):
        self.product_data = product_data
        self.store_url = store_url
        self.parser = HTMLParser()  # Initialize the parser

    def scrape_reviews(self):
        for product in self.product_data:
            product_handle = product.get("handle")
            product_sku = self.get_product_sku(product)  # Get SKU if needed
            reviews = self.get_reviews_for_product(product_handle, product_sku)
            save_review_data(reviews, product_handle)  # Save reviews under the correct product folder
            log_info(f"Scraped {len(reviews)} reviews for product '{product['title']}'")

    def get_reviews_for_product(self, product_handle, product_sku):
        reviews_url = self.build_reviews_api_url(product_sku)
        log_debug(f"Fetching reviews from: {reviews_url}")
        reviews = []
        page = 1

        while True:
            paginated_url = f"{reviews_url}&page={page}&per_page=5000"
            response = requests.get(paginated_url)
            
            if response.status_code == 200:
                data = response.json()
                timeline_reviews = data.get("timeline", [])
                
                if not timeline_reviews:
                    break  # Exit if no more reviews are available

                reviews.extend(self.parse_reviews(timeline_reviews))
                log_debug(f"Fetched {len(timeline_reviews)} reviews for product handle: {product_handle}")
                page += 1
            else:
                log_info(f"Failed to scrape reviews for product handle '{product_handle}', page {page}")
                break

        return reviews

    def build_reviews_api_url(self, product_sku):
        base_api_url = "https://api.reviews.io/timeline/data"
        return f"{base_api_url}?type=product_review&store={self.store_url}&sku={product_sku}&sort=date_desc&include_sentiment_analysis=true"

    def get_product_sku(self, product):
        variants = product.get("variants", [])
        if variants:
            return variants[0].get("sku")
        return None

    def parse_reviews(self, timeline_reviews):
        parsed_reviews = []
        for idx, review in enumerate(timeline_reviews):
            review_data = review.get('_source', {})
            cleaned_comments = self.parser.parse_html_to_text(review_data.get("comments", ""))  # Clean review comments
            cleaned_author = self.parser.parse_html_to_text(review_data.get("author", ""))  # Clean author

            parsed_reviews.append({
                "author": cleaned_author,
                "rating": review_data.get("rating"),
                "comments": cleaned_comments,
                "product_name": self.parser.parse_html_to_text(review_data.get("product_name", "")),  # Clean product name
                "date_created": review_data.get("date_created"),
                "sku": review_data.get("sku"),
                "order_id": review_data.get("order_id"),
                "source": review_data.get("source")
            })
        return parsed_reviews
