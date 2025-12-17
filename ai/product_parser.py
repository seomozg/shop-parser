from .deepseek_client import DeepSeekClient
from extractor.images import ImageExtractor
import os
import config

class ProductParser:
    """Orchestrates product data extraction and image handling"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.ai_client = DeepSeekClient()
        self.image_extractor = ImageExtractor(base_url)

    def parse_product_page(self, raw_content, page_url):
        """Parse a single product page and return structured product data"""
        if not raw_content:
            return None

        # Try to extract product data from structured data (JSON-LD)
        product_data = self._extract_from_structured_data(raw_content, page_url)

        if not product_data:
            print(f"No structured data found for URL: {page_url}")
            return None

        print(f"Extracted product: {product_data.get('title', 'Unknown')}")

        # Process images from structured data
        structured_images = product_data.get('images', [])
        processed_images = []

        for img_url in structured_images[:5]:  # Limit to 5 images
            if img_url and isinstance(img_url, str):
                processed_images.append({
                    'url': img_url,
                    'alt': '',
                    'filename': self.image_extractor._generate_filename(img_url)
                })

        product_data['images'] = processed_images
        product_data['url'] = page_url

        # Clean and normalize data
        product_data = self._normalize_product_data(product_data)

        return product_data

    def _normalize_product_data(self, product_data):
        """Normalize and clean product data"""
        # Ensure title is clean
        if 'title' in product_data:
            product_data['title'] = product_data['title'].strip()

        # Ensure description is clean
        if 'description' in product_data:
            product_data['description'] = product_data['description'].strip()

        # Normalize prices - remove currency symbols and extra spaces
        for price_field in ['price', 'old_price']:
            if price_field in product_data and product_data[price_field]:
                # Extract numeric value
                import re
                price_str = str(product_data[price_field])
                # Find price pattern (digits, decimal point, comma)
                match = re.search(r'[\d,]+\.?\d*', price_str.replace(' ', ''))
                if match:
                    price = match.group()
                    # Remove commas and convert to float then back to string for consistency
                    try:
                        numeric_price = float(price.replace(',', ''))
                        product_data[price_field] = f"{numeric_price:.2f}"
                    except ValueError:
                        product_data[price_field] = price
                else:
                    product_data[price_field] = ""

        # Ensure currency is uppercase
        if 'currency' in product_data and product_data['currency']:
            product_data['currency'] = product_data['currency'].upper()

        return product_data

    def _extract_from_structured_data(self, raw_content, page_url):
        """Extract product data from JSON-LD structured data or fallback to meta tags"""
        structured_data = raw_content.get('structured_data', [])

        # First try JSON-LD structured data
        for data in structured_data:
            if isinstance(data, dict) and data.get('@type') == 'Product':
                product_data = {
                    'is_product': True,
                    'title': data.get('name', ''),
                    'description': data.get('description', ''),
                    'images': []
                }

                # Extract images
                if 'image' in data:
                    images = data['image']
                    if isinstance(images, list):
                        product_data['images'] = images
                    elif isinstance(images, str):
                        product_data['images'] = [images]

                # Extract price and currency from offers
                offers = data.get('offers', {})
                if isinstance(offers, dict):
                    product_data['price'] = str(offers.get('price', ''))
                    product_data['currency'] = offers.get('priceCurrency', '')
                    # Check for old price in additional offers
                    if 'lowPrice' in offers and 'highPrice' in offers:
                        product_data['old_price'] = str(offers.get('highPrice', ''))
                        product_data['price'] = str(offers.get('lowPrice', ''))
                elif isinstance(offers, list) and offers:
                    # Take first offer
                    offer = offers[0]
                    product_data['price'] = str(offer.get('price', ''))
                    product_data['currency'] = offer.get('priceCurrency', '')

                return product_data

        # Fallback to meta tags
        meta_tags = raw_content.get('meta_tags', {})
        if meta_tags:
            product_data = {
                'is_product': True,
                'title': (meta_tags.get('og:title') or
                         meta_tags.get('twitter:title') or
                         meta_tags.get('title') or
                         raw_content.get('title', '')),
                'description': (meta_tags.get('og:description') or
                               meta_tags.get('twitter:description') or
                               meta_tags.get('description') or
                               ''),
                'images': []
            }

            # Extract price from meta tags
            price = (meta_tags.get('product:price:amount') or
                    meta_tags.get('og:price:amount'))
            if price:
                product_data['price'] = str(price)
                product_data['currency'] = (meta_tags.get('product:price:currency') or
                                          meta_tags.get('og:price:currency') or
                                          'USD')

            # Extract images from meta tags
            og_image = meta_tags.get('og:image')
            if og_image:
                product_data['images'] = [og_image]

            # If we have at least a title, consider it a product
            if product_data['title']:
                return product_data

        # Last resort: extract from HTML content directly
        return self._extract_from_html_content(raw_content)

    def download_product_images(self, product_data, output_dir, product_id):
        """Download images for a product with proper naming"""
        if not product_data or 'images' not in product_data:
            return []

        downloaded_images = []
        images_dir = os.path.join(output_dir, 'images')

        # Ensure images directory exists
        os.makedirs(images_dir, exist_ok=True)

        for i, image_data in enumerate(product_data['images'], 1):
            # Generate filename with product ID
            ext = self._get_image_extension(image_data['filename'])
            filename = f"{product_id}-{i}.{ext}"
            filepath = os.path.join(images_dir, filename)

            # Download image
            if self.image_extractor.download_image(image_data['url'], filepath):
                downloaded_images.append(filename)
            else:
                print(f"Failed to download image: {image_data['url']}")

        return downloaded_images

    def _get_image_extension(self, filename):
        """Extract or determine image extension"""
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                return ext

        # Default to webp as specified in README
        return 'webp'

    def _extract_from_html_content(self, raw_content):
        """Extract product data from HTML content as last resort"""
        import re

        product_data = {
            'is_product': True,
            'title': raw_content.get('title', ''),
            'description': '',
            'price': '',
            'currency': 'EUR',  # Default for this site
            'images': []
        }

        # Use images from raw_content
        images = raw_content.get('images', [])
        if images:
            # Take first few images
            product_data['images'] = [img['src'] for img in images[:5] if img.get('src')]

        # Try to extract price from text content
        text_content = raw_content.get('text_content', '')
        if text_content:
            # Look for price patterns like €123.45, 123.45€, $123.45, etc.
            price_patterns = [
                r'€\s*([\d,]+\.?\d*)',  # €123.45
                r'\$\s*([\d,]+\.?\d*)',  # $123.45
                r'£\s*([\d,]+\.?\d*)',  # £123.45
                r'([\d,]+\.?\d*)\s*€',  # 123.45€
                r'([\d,]+\.?\d*)\s*\$', # 123.45$
                r'([\d,]+\.?\d*)\s*£',  # 123.45£
            ]

            for pattern in price_patterns:
                match = re.search(pattern, text_content)
                if match:
                    product_data['price'] = match.group(1)
                    # Set currency based on symbol
                    if '€' in match.group(0):
                        product_data['currency'] = 'EUR'
                    elif '$' in match.group(0):
                        product_data['currency'] = 'USD'
                    elif '£' in match.group(0):
                        product_data['currency'] = 'GBP'
                    break

        # Try to get description from headings or text
        headings = raw_content.get('headings', [])
        if headings:
            # Use first H1 or H2 as potential description
            for heading in headings:
                if heading['level'] <= 2 and len(heading['text']) > 10:
                    product_data['description'] = heading['text']
                    break

        return product_data if product_data['title'] else None
