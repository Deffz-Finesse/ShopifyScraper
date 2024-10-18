## ProductScrape/src/parser.py

import html
import re
import os
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from urllib.parse import urlparse
import warnings

# Suppress the warning for inputs that look like file paths or locators
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

class HTMLParser:
    def __init__(self, keep_links=False):
        self.keep_links = keep_links

    def parse_html_to_text(self, html_content):
        # Check if the input resembles a URL or a file path and skip parsing
        if self._is_url(html_content) or self._is_file_path(html_content):
            return html_content  # Return the content as-is
        
        decoded_content = html.unescape(html_content)
        soup = BeautifulSoup(decoded_content, "html.parser")
        
        self._remove_unwanted_tags(soup)
        self._clean_attributes(soup)
        
        if not self.keep_links:
            self._strip_links(soup)
        
        clean_text = soup.get_text(separator=' ', strip=True)
        clean_text = self._normalize_whitespace(clean_text)
        clean_text = self._fix_special_cases(clean_text)
        
        return clean_text

    def _is_url(self, content):
        # Check if content resembles a URL
        try:
            result = urlparse(content)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _is_file_path(self, content):
        # Check if the content resembles a file path (e.g., ends with a common file extension)
        return os.path.isfile(content) or re.match(r".*\.(html?|txt|json|csv|xml)$", content)

    def _remove_unwanted_tags(self, soup):
        for tag in soup(["script", "style", "iframe", "img", "noscript", "embed", "object", "video", "audio"]):
            tag.decompose()

    def _strip_links(self, soup):
        for a in soup.find_all('a'):
            a.unwrap()

    def _clean_attributes(self, soup):
        for tag in soup.find_all(True):
            tag.attrs = {}

    def _normalize_whitespace(self, text):
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _fix_special_cases(self, text):
        special_char_map = {
            r'\u00A0': ' ',  # Non-breaking space
            r'&nbsp;': ' ',  # Non-breaking space (HTML)
            r'&amp;': '&',   # Ampersand
            r'&quot;': '"',  # Double quotes
            r'&lt;': '<',    # Less than
            r'&gt;': '>',    # Greater than
            r'&#39;': "'",   # Single quote
            r'&apos;': "'",  # Apostrophe
            r'&cent;': '¢',  # Cent sign
            r'&pound;': '£', # Pound sterling
            r'&yen;': '¥',   # Yen sign
            r'&euro;': '€',  # Euro sign
            r'&copy;': '©',  # Copyright
            r'&reg;': '®',   # Registered trademark
            r'&trade;': '™', # Trademark
            r'&sect;': '§',  # Section sign
            r'&deg;': '°',   # Degree symbol
            r'&plusmn;': '±',# Plus-minus sign
            r'&para;': '¶',  # Paragraph symbol
            r'&middot;': '·',# Middle dot
            r'&ndash;': '–', # En dash
            r'&mdash;': '—', # Em dash
            r'&lsquo;': '‘', # Left single quotation mark
            r'&rsquo;': '’', # Right single quotation mark
            r'&ldquo;': '“', # Left double quotation mark
            r'&rdquo;': '”', # Right double quotation mark
            r'&bull;': '•',  # Bullet point
            r'&hellip;': '…',# Ellipsis
            r'&iquest;': '¿', # Inverted question mark
            r'&iexcl;': '¡',  # Inverted exclamation mark
            r'&laquo;': '«',  # Left angle quote
            r'&raquo;': '»',  # Right angle quote
        }

        for entity, replacement in special_char_map.items():
            text = re.sub(entity, replacement, text)

        # Remove any leftover Unicode sequences like \uXXXX
        text = re.sub(r'\\u[0-9A-Fa-f]{4}', '', text)

        return text

    def _handle_lists_and_tables(self, soup):
        for ul in soup.find_all('ul'):
            self._convert_to_plain_text(ul, bullet_point='* ')
        
        for ol in soup.find_all('ol'):
            self._convert_to_plain_text(ol, numbered=True)
        
        for table in soup.find_all('table'):
            self._convert_table_to_text(table)

    def _convert_to_plain_text(self, list_tag, bullet_point='- ', numbered=False):
        for idx, li in enumerate(list_tag.find_all('li'), 1):
            prefix = f"{bullet_point}" if not numbered else f"{idx}. "
            li.insert_before(prefix)
            li.unwrap()

        list_tag.unwrap()

    def _convert_table_to_text(self, table):
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(separator=' ', strip=True) for td in tr.find_all(['td', 'th'])]
            rows.append('\t'.join(cells))

        table_text = '\n'.join(rows)
        table.insert_before(table_text)
        table.decompose()
