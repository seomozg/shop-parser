import csv
import os
from typing import List, Dict

class CSVWriter:
    """Handles writing product data to CSV format"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.catalog_path = os.path.join(output_dir, "catalog.csv")
        os.makedirs(output_dir, exist_ok=True)

    def write_products(self, products: List[Dict], append: bool = False):
        """Write products to CSV file"""
        if not products:
            return

        # Prepare data for CSV
        csv_data = []
        for product in products:
            row = self._product_to_csv_row(product)
            if row:
                csv_data.append(row)

        if not csv_data:
            return

        # Write to CSV
        mode = 'a' if append and os.path.exists(self.catalog_path) else 'w'
        header = not (append and os.path.exists(self.catalog_path))

        with open(self.catalog_path, mode, newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'url', 'title', 'description', 'price', 'old_price', 'currency', 'images']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if header:
                writer.writeheader()

            for row in csv_data:
                writer.writerow(row)

        print(f"Written {len(csv_data)} products to {self.catalog_path}")

    def _product_to_csv_row(self, product: Dict) -> Dict:
        """Convert product data to CSV row format"""
        # Format images as comma-separated string
        images_str = ""
        if 'images' in product and product['images']:
            image_filenames = []
            for img in product['images']:
                if isinstance(img, dict) and 'filename' in img:
                    image_filenames.append(img['filename'])
                elif isinstance(img, str):
                    image_filenames.append(img)
            images_str = ",".join(image_filenames)

        return {
            'id': product.get('id', ''),
            'url': product.get('url', ''),
            'title': product.get('title', ''),
            'description': product.get('description', ''),
            'price': product.get('price', ''),
            'old_price': product.get('old_price', ''),
            'currency': product.get('currency', ''),
            'images': images_str
        }

    def get_existing_product_ids(self) -> set:
        """Get set of existing product IDs from CSV"""
        if not os.path.exists(self.catalog_path):
            return set()

        try:
            with open(self.catalog_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                return {row['id'] for row in reader if row.get('id')}
        except Exception:
            return set()

    def append_product(self, product: Dict):
        """Append a single product to CSV"""
        self.write_products([product], append=True)
