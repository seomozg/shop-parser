import os
import shutil
from typing import List, Dict

class ImageStore:
    """Manages storage of downloaded product images"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)

    def store_product_images(self, product_data: Dict, product_id: str) -> List[str]:
        """Store images for a product and return list of stored filenames"""
        if not product_data or 'images' not in product_data:
            return []

        stored_images = []

        for i, image_data in enumerate(product_data['images'], 1):
            if isinstance(image_data, dict) and 'filename' in image_data:
                # Get original filename
                original_filename = image_data['filename']

                # Generate new filename with product ID
                ext = self._get_extension(original_filename)
                new_filename = f"{product_id}-{i}.{ext}"
                new_filepath = os.path.join(self.images_dir, new_filename)

                # If image was already downloaded to a temp location, move it
                # (In our case, images are downloaded directly to final location)
                # But we can implement logic to handle temp downloads if needed

                stored_images.append(new_filename)

        return stored_images

    def get_image_path(self, filename: str) -> str:
        """Get full path for an image filename"""
        return os.path.join(self.images_dir, filename)

    def cleanup_old_images(self, keep_product_ids: List[str]):
        """Remove images for products not in the keep list"""
        if not os.path.exists(self.images_dir):
            return

        keep_files = set()
        for product_id in keep_product_ids:
            # Find all files starting with this product ID
            for filename in os.listdir(self.images_dir):
                if filename.startswith(f"{product_id}-"):
                    keep_files.add(filename)

        # Remove files not in keep list
        for filename in os.listdir(self.images_dir):
            if filename not in keep_files:
                filepath = os.path.join(self.images_dir, filename)
                try:
                    os.remove(filepath)
                    print(f"Removed old image: {filename}")
                except Exception as e:
                    print(f"Error removing {filename}: {e}")

    def get_product_images(self, product_id: str) -> List[str]:
        """Get all image filenames for a product"""
        if not os.path.exists(self.images_dir):
            return []

        images = []
        for filename in os.listdir(self.images_dir):
            if filename.startswith(f"{product_id}-"):
                images.append(filename)

        # Sort by number
        images.sort(key=lambda x: self._extract_image_number(x))
        return images

    def _get_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                return ext
        return 'webp'  # Default as per README

    def _extract_image_number(self, filename: str) -> int:
        """Extract image number from filename like '123-1.webp'"""
        try:
            # Split by '-' and take the last part before extension
            parts = filename.split('-')
            if len(parts) >= 2:
                num_part = parts[-1].split('.')[0]
                return int(num_part)
        except (ValueError, IndexError):
            pass
        return 0

    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        if not os.path.exists(self.images_dir):
            return {'total_images': 0, 'total_size_mb': 0}

        total_images = 0
        total_size = 0

        for filename in os.listdir(self.images_dir):
            filepath = os.path.join(self.images_dir, filename)
            if os.path.isfile(filepath):
                total_images += 1
                total_size += os.path.getsize(filepath)

        return {
            'total_images': total_images,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
