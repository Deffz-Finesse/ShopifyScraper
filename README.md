
# 🚀 ProductScrape

**ProductScrape** is an asynchronous web scraping tool designed to extract product data and customer reviews from Shopify-based eCommerce websites. It gathers key product information such as titles, pricing, and variants, and seamlessly captures product reviews from third-party services like Reviews.io.

## ✨ Features

- ⚡ **Asynchronous Scraping**: Efficiently scrape product data and reviews concurrently across multiple Shopify stores.
- 📄 **Paginated Data Fetching**: Handles pagination for both product collections and reviews to ensure all available data is captured.
- 📝 **Review Aggregation**: Fetch product reviews from Reviews.io via SKU-based API queries, with the ability to extend support for other review platforms.
- 🔍 **Duplicate Detection**: Ensures no duplicate product data is scraped by loading previously scraped product information.
- 🔧 **Customizable Store Input**: Accepts Shopify store URLs from a predefined file or user input during runtime.
- 🛠️ **Logging**: Provides detailed logging for both product and review scraping processes to aid debugging and tracking.

## 🛠️ Requirements

- Python 3.8+

### Setting Up the Virtual Environment

1. Create a virtual environment called `myenv`:

```bash
python -m venv myenv
```

2. Activate the virtual environment:

- **Windows**:
  ```bash
  myenv\Scripts\activate
  ```
- **macOS/Linux**:
  ```bash
  source myenv/bin/activate
  ```

To install the required dependencies, run:

```bash
pip install -r requirements.txt
```

## 🗂️ Project Structure

```bash
ProductScrape/
│
├── data/                   # Data storage for scraped products and reviews
│   ├── products/            # Directory containing JSON files for each scraped product
│   ├── product_list.json    # Tracks previously scraped product data to avoid duplication
│   └── stores.txt           # List of Shopify store URLs to scrape
│
├── src/                     # Source code directory
│   ├── __init__.py
│   ├── product_info.py      # Scraper class for extracting product information
│   ├── review_scraper.py    # Scraper class for fetching reviews via Reviews.io API
│   └── utils.py             # Utility functions (logging, file handling, concurrency)
│
├── main.py                  # Main script for scraping products and reviews concurrently
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

## 🚦 How It Works

### 1. Scraping Products

The tool scrapes product information from Shopify stores, including titles, vendors, pricing, variants, tags, and descriptions. This is handled by the `ProductInfoScraper` class, which supports paginated data fetching from Shopify collections or the main product listing.

### 2. Scraping Reviews

After product data is scraped, reviews are fetched from Reviews.io based on product SKUs. This process is managed by the `ReviewScraper` class, which retrieves review information (author, rating, comments, etc.) and handles pagination to ensure all available reviews are captured.

### 3. Concurrent Scraping

The `main.py` script orchestrates the scraping process, managing both product and review scraping concurrently with a 5-second delay for review scraping. This ensures product data is captured first, and reviews are scraped only after the product data is available.

## 💻 Usage

### 1. Running the Scraper

To start scraping, run the `main.py` script:

```bash
python main.py
```

You will be prompted to either use the list of Shopify stores in `stores.txt` or enter a custom store URL during runtime.

### 2. Data Storage

- **Products**: Each product’s data is stored in a folder named after the product handle under `data/products/{product_handle}/product.json`.
- **Reviews**: Each review is stored as an individual JSON file within the respective product’s folder under `data/products/{product_handle}/reviews`.

### 3. Handling Duplicates

The scraper loads previously scraped product information from `data/product_list.json` to avoid duplication. Each product handle is checked against this file before new data is scraped.

## ⚙️ Configuration

- **Stores List**: Add Shopify store URLs to the `data/stores.txt` file to automate scraping across multiple stores. One URL per line.
- **Review API**: The `review_scraper.py` script is designed to work with Reviews.io but can be extended to support other review platforms by modifying the `build_reviews_api_url` function.

## 🚀 Extending the Project

### 1. Support for Other eCommerce Platforms

To extend the tool for other eCommerce platforms, the `ProductInfoScraper` class can be modified to fetch product data from different APIs or store structures.

### 2. Custom Review Platforms

Currently, the tool works with Reviews.io. To add support for other review platforms, update the `ReviewScraper` class with the appropriate API endpoint and review structure.

## 📝 Logging

Scraping progress and issues are logged in the `data/scrape_log.txt` file. Console output is also enabled for real-time feedback during the scraping process.

## 🔮 Future Improvements

- **Dynamic Delay**: Introduce dynamic delay timing for review scraping based on the size of the store.
- **Error Handling**: Implement better error handling for failed or missing store URLs.
- **Rate Limiting**: Add rate limiting mechanisms to avoid API throttling, especially for large-scale scraping.

## 📜 License

This project is open-source and licensed under the MIT License.
