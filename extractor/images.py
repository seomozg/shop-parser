import requests
from urllib.parse import urljoin, urlparse
import os
import re
import config
from PIL import Image
from io import BytesIO

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

        print(f"DEBUG: Found {len(images)} candidate images for {page_url}")

        # Filter by actual image size - keep largest and similar sized images
        if images:
            images_with_size = []
            for img in images:
                dims = self._get_image_dimensions(img['url'])
                if dims:
                    width, height, file_size = dims
                    area = width * height
                    # Skip likely background images (too large or named background)
                    if not self._is_background_image(img['url'], width, height):
                        images_with_size.append({
                            **img,
                            'width': width,
                            'height': height,
                            'area': area,
                            'file_size': file_size
                        })

            print(f"DEBUG: {len(images_with_size)} images passed size check")

            if images_with_size:
                # Find the largest image
                max_area = max(img['area'] for img in images_with_size)

                # Keep images that are at least 70% of the largest image size
                # AND have minimum width of 200 pixels AND minimum area of 5000 pixels
                filtered_images = [
                    img for img in images_with_size
                    if img['area'] >= max_area * 0.7 and img['area'] >= 5000 and img['width'] >= 200
                ]

                print(f"DEBUG: {len(filtered_images)} images passed final filter")

                # If no images meet the criteria, take just the largest one
                if not filtered_images and images_with_size:
                    filtered_images = [max(images_with_size, key=lambda x: x['area'])]
                    print(f"DEBUG: Using fallback - largest image only")

                # Sort by area descending and return (limit to 3 images per product)
                filtered_images.sort(key=lambda x: x['area'], reverse=True)
                return filtered_images[:3]

        return []

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
        if any(pattern in url_lower for pattern in ['icon', 'logo', 'favicon', 'avatar', 'profile']):
            return False

        # Skip small images (likely icons)
        if any(dim in url_lower for dim in ['16x16', '32x32', '64x64', '100x100', '128x128']):
            return False

        # Skip images with UI/navigation patterns
        if any(pattern in url_lower for pattern in ['nav', 'menu', 'header', 'footer', 'sidebar', 'widget', 'banner']):
            return False

        # Skip social media and sharing icons
        if any(pattern in url_lower for pattern in ['facebook', 'twitter', 'instagram', 'youtube', 'linkedin', 'share']):
            return False

        # Skip SVG and icon formats
        if url_lower.endswith(('.svg', '.ico', '.gif')):
            return False

        # Accept all common image formats
        if url_lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return True

        return False

    def _is_background_image(self, img_url, width, height):
        """Determine if image is likely a background image"""
        url_lower = img_url.lower()

        # Skip images with background in URL
        if 'background' in url_lower or 'bg' in url_lower:
            return True

        # Skip very large images (likely backgrounds or banners)
        # Typical screen sizes: 1920x1080, 2560x1440, etc.
        if width > 3000 or height > 2000:
            return True

        # Skip images that are extremely wide (banners)
        if width > height * 3:
            return True

        return False

    def _get_image_dimensions(self, img_url):
        """Get image dimensions (width, height) and size info"""
        try:
            response = self.session.get(img_url, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                return None

            # Check file size (must be >= 10KB to filter out tiny icons)
            content_length = len(response.content)
            if content_length < 10 * 1024:  # 10KB in bytes
                return None

            img = Image.open(BytesIO(response.content))
            width, height = img.size

            # Return dimensions + file size info
            return (width, height, content_length)

        except Exception as e:
            print(f"Error getting dimensions for {img_url}: {e}")
            return None

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
