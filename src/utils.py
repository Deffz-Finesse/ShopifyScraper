## ProductScrape/src/utils.py

import os
import json
import logging
import aiofiles
import aiohttp
import sys
import time
import threading
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from timeit import default_timer as timer
import signal
import gzip
import asyncio

# ! Custom exception for graceful shutdown
class ScrapeInterrupted(Exception):
    pass


# * Setup logging as a single function
def setup_logging(log_dir="data", log_filename="scrape_log.json"):
    os.makedirs(log_dir, exist_ok=True)
    log_filepath = os.path.join(log_dir, log_filename)

    logging.basicConfig(
        filename=log_filepath,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w",
    )

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # ? Suppress console logs
    logger.handlers = [
        h for h in logger.handlers if not isinstance(h, logging.StreamHandler)
    ]

    return logger  # * Return logger object


# * Initialize logger and store logging functions in one object
log = setup_logging()

# * Terminal-based loading animation and progress counter
def terminal_progress_control(
    products_count,
    reviews_count,
    stop_event,
    show_reviews=True,
    show_products=True,
    update_delay=0.5,
):
    loading_chars = "|/-\\"
    idx = 0
    start_time = timer()

    while not stop_event.is_set():
        status_line = (
            f"\r{loading_chars[idx % len(loading_chars)]} Scraping in progress..."
        )
        idx += 1

        # * Combine product and review counts into one string
        if show_products:
            status_line += f" Products Scraped: {products_count[0]}"
        if show_reviews:
            status_line += f" Reviews Scraped: {reviews_count[0]}"

        # * Only flush once after writing the status
        sys.stdout.write(status_line)
        sys.stdout.flush()
        time.sleep(update_delay)

    # * Final status after scraping finishes
    elapsed_time = timer() - start_time
    sys.stdout.write(
        f"\rFinished! Scraping took {elapsed_time:.2f} seconds. {' ' * 50}\n"
    )
    sys.stdout.flush()


# * Asynchronous function to save data to a file with error handling
async def save_data(filepath, data):
    try:
        os.makedirs(
            os.path.dirname(filepath), exist_ok=True
        )  # * Centralized directory creation
        async with aiofiles.open(filepath, "wb") as file:
            compressed_data = gzip.compress(
                json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")
            )
            await file.write(compressed_data)
    except (OSError, IOError) as e:
        log.error(f"Failed to save data to {filepath}: {e}")


# * Unified data saving function
async def save_data_generic(data, folder, filename):
    file_path = os.path.join(folder, filename)
    await save_data(file_path, data)


# * Load previously scraped products to avoid duplicates
async def load_scraped_products(filepath="data/product_list.json.gz"):
    if os.path.exists(filepath):
        try:
            async with aiofiles.open(filepath, "rb") as file:
                compressed_content = await file.read()
                content = gzip.decompress(compressed_content).decode("utf-8")
                return (
                    json.loads(content) or {}
                )  # * Load the JSON content, return empty dict if invalid
        except (OSError, IOError, json.JSONDecodeError) as e:
            log.error(f"Error loading scraped products: {e}")
            return {}
    return {}


# * Save scraped products to avoid duplicates
async def save_scraped_products(scraped_products, filepath="data/product_list.json.gz"):
    await save_data(filepath, scraped_products)
    log.info(f"Updated product_list.json.gz with {len(scraped_products)} products.")


# * Check if a product is a duplicate based on its handle
def is_duplicate(product_handle, scraped_products):
    if product_handle in scraped_products:
        log.info(f"Duplicate found: {product_handle}")
        return True
    return False


# * Batch Save for Efficiency with optimized duplicate check
async def batch_save_products(batch, scraped_products, batch_size=25):
    new_products = set()  # * Use set for faster lookups

    for product in batch:
        product_handle = product["handle"]

        if product_handle not in scraped_products:
            await save_data_generic(
                product, f"data/Products/{product_handle}", "product.json.gz"
            )
            new_products.add(product_handle)
        else:
            log.info(f"Duplicate skipped for {product_handle}")

    if new_products:
        scraped_products.update({handle: True for handle in new_products})
        await save_scraped_products(scraped_products)

    batch.clear()


# ! Asynchronous function to fetch a URL with retry mechanism
async def fetch_url(session, url, retries=3, delay=1):
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                response.raise_for_status()  # ! Raise an exception for bad status codes
                return await response.text()  # * Return the response body as text
        except aiohttp.ClientError as e:
            if attempt < retries - 1:
                log.warning(
                    f"Error fetching {url}, retrying ({attempt + 1}/{retries}): {e}"
                )
                await asyncio.sleep(delay)
                delay *= 2  # * Exponential backoff
            else:
                log.error(f"Failed to fetch {url} after {retries} retries: {e}")
                return None


# * Function to track progress during scraping
async def track_progress_during_scraping(
    scraping_future,
    products_scraped,
    reviews_scraped,
    show_reviews=True,
    show_products=True,
):
    stop_event = threading.Event()
    animation_thread = threading.Thread(
        target=terminal_progress_control,
        args=(
            products_scraped,
            reviews_scraped,
            stop_event,
            show_reviews,
            show_products,
        ),
    )

    # * Start the animation
    animation_thread.start()

    try:
        await scraping_future  # Ensure this is an awaitable future
    finally:
        stop_event.set()
        animation_thread.join()  # * Wait for the animation to stop


# * Function to zip the 'Products' folder after scraping
async def zip_products_folder(folder="data/Products"):
    if os.path.exists(folder):
        try:
            zip_file_path = shutil.make_archive(folder, "zip", folder)
            log.info(f"Zipped products folder: {zip_file_path}")
        except (OSError, IOError) as e:
            log.error(f"Failed to zip folder {folder}: {e}")
    else:
        log.info(f"Products folder not found. No zipping performed.")


# ! Signal handler for graceful shutdown
def signal_handler(signal, frame):
    log.info("Scraping interrupted by user.")
    raise ScrapeInterrupted()


# * Register the signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)
