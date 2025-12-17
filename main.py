#!/usr/bin/env python3
"""
Universal E-commerce Parser
Scrapes any online store using AI-powered product detection
"""

import sys
import os
from urllib.parse import urlparse
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler.sitemap import SitemapParser
from crawler.fetcher import PageFetcher
from crawler.filters import URLFilter
from extractor.raw_content import RawContentExtractor
from ai.product_parser import ProductParser
from storage.csv_writer import CSVWriter
from storage.image_store import ImageStore
import config

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python main.py <website_url>")
        print("Example: python main.py https://atelierhome-art.com")
        sys.exit(1)

    website_url = sys.argv[1].rstrip('/')
    print(f"Starting e-commerce parser for: {website_url}")

    # Validate URL
    try:
        parsed = urlparse(website_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL")
    except Exception as e:
        print(f"Error: Invalid URL format - {e}")
        sys.exit(1)

    # Initialize components
    try:
        print("Initializing components...")
        sitemap_parser = SitemapParser(website_url)
        url_filter = URLFilter(website_url)
        content_extractor = RawContentExtractor()
        product_parser = ProductParser(website_url)
        csv_writer = CSVWriter("output")
        image_store = ImageStore("output")

        # Get all URLs from sitemap
        print("Fetching sitemap URLs...")
        all_urls = sitemap_parser.get_all_urls()
        print(f"Found {len(all_urls)} URLs in sitemap")

        # Filter URLs
        filtered_urls = url_filter.filter_urls(all_urls)
        print(f"Filtered to {len(filtered_urls)} relevant URLs")

        # Process pages
        products_found = 0
        products = []

        with PageFetcher() as fetcher:
            for i, url in enumerate(filtered_urls, 1):
                print(f"Processing {i}/{len(filtered_urls)}: {url}")

                try:
                    # Fetch page content
                    html_content = fetcher.fetch_page(url)
                    if not html_content:
                        continue

                    # Extract raw content
                    raw_content = content_extractor.extract_content(html_content)
                    if not raw_content:
                        continue

                    # Parse product data
                    product_data = product_parser.parse_product_page(raw_content, url)
                    if product_data:
                        # Add product ID
                        product_data['id'] = str(products_found + 1)

                        # Download images
                        downloaded_images = product_parser.download_product_images(
                            product_data, "output", product_data['id']
                        )

                        # Update product data with downloaded image filenames
                        product_data['images'] = downloaded_images

                        products.append(product_data)
                        products_found += 1

                        print(f"✓ Found product: {product_data.get('title', 'Unknown')}")

                    # Rate limiting
                    time.sleep(1)

                except Exception as e:
                    print(f"Error processing {url}: {e}")
                    continue

        # Save results
        if products:
            print(f"\nSaving {len(products)} products...")
            csv_writer.write_products(products)

            # Print summary
            print("\n" + "="*50)
            print("PARSING COMPLETE")
            print("="*50)
            print(f"Products found: {len(products)}")
            print(f"Output CSV: output/catalog.csv")
            print(f"Output images: output/images/")

            stats = image_store.get_storage_stats()
            print(f"Images downloaded: {stats['total_images']}")
            print(".2f")
        else:
            print("No products found on the website.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
