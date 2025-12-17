import requests
from urllib.parse import urljoin, urlparse
import os
import re
import config

class ImageExtractor:
    """Handles image extraction and download"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

        # Skip small icons and trackers
        self.skip_patterns = [
            'icon', 'logo', 'favicon', 'tracking', 'pixel',
            'analytics', 'social', 'share', 'button'
        ]

    def extract_product_images(self, raw_content, page_url):
        """Extract and filter product images from raw content"""
        if not raw_content or 'images' not in raw_content:
            return []

        images = []
        seen_urls = set()

        for img_data in raw_content['images']:
            img_url = self._resolve_image_url(img_data['src'], page_url)

            if not img_url or img_url in seen_urls:
                continue

            # Filter out non-product images
            if self._is_product_image(img_url, img_data.get('alt', '')):
                images.append({
                    'url': img_url,
                    'alt': img_data.get('alt', ''),
                    'filename': self._generate_filename(img_url)
                })
                seen_urls.add(img_url)

        # Prefer larger images
        images.sort(key=lambda x: self._get_image_size_score(x['url']), reverse=True)

        return images[:10]  # Limit to 10 images per product

    def _resolve_image_url(self, img_src, page_url):
        """Resolve relative image URLs to absolute URLs"""
        if not img_src:
            return None

        if img_src.startswith(('http://', 'https://')):
            return img_src

        # Handle relative URLs
        return urljoin(page_url, img_src)

    def _is_product_image(self, img_url, alt_text):
        """Determine if image is likely a product image"""
        url_lower = img_url.lower()

        # Skip obvious icons and logos
        if any(pattern in url_lower for pattern in ['icon', 'logo', 'favicon']):
            return False

        # Skip small images (likely icons)
        if any(dim in url_lower for dim in ['16x16', '32x32', '64x64']):
            return False

        # Skip SVG and icon formats
        if url_lower.endswith(('.svg', '.ico')):
            return False

        # Accept all common image formats
        if url_lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return True

        return False

    def _get_image_size_score(self, img_url):
        """Score image based on likely size (rough heuristic)"""
        url_lower = img_url.lower()

        # Higher score for large/master images
        if any(term in url_lower for term in ['large', 'master', 'original', 'full']):
            return 10

        # Medium score for standard sizes
        if any(term in url_lower for term in ['medium', 'normal']):
            return 5

        # Lower score for thumbnails
        if any(term in url_lower for term in ['thumb', 'small', 'tiny']):
            return 1

        return 3  # Default score

    def _generate_filename(self, img_url):
        """Generate filename for downloaded image"""
        parsed = urlparse(img_url)
        path = parsed.path

        # Extract filename from URL
        filename = os.path.basename(path)

        # If no extension, assume jpg
        if not filename or '.' not in filename:
            filename = 'image.jpg'

        # Clean filename
        filename = re.sub(r'[^\w\-_\.]', '', filename)

        return filename

    def download_image(self, img_url, output_path):
        """Download image to specified path"""
        try:
            response = self.session.get(img_url)
            response.raise_for_status()

            # Verify it's actually an image
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                return False

            # Save image
            with open(output_path, 'wb') as f:
                f.write(response.content)

            return True

        except Exception as e:
            print(f"Error downloading image {img_url}: {e}")
            return False
