from bs4 import BeautifulSoup
import json
import re

class RawContentExtractor:
    """Extracts raw content from HTML pages"""

    def extract_content(self, html_content):
        """Extract raw content from HTML"""
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, 'html.parser')

        content = {
            'title': self._extract_title(soup),
            'headings': self._extract_headings(soup),
            'text_content': self._extract_text_content(soup),
            'images': self._extract_images(soup),
            'structured_data': self._extract_structured_data(soup),
            'meta_tags': self._extract_meta_tags(soup)
        }

        return content

    def _extract_title(self, soup):
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.text.strip() if title_tag else ""

    def _extract_headings(self, soup):
        """Extract h1-h3 headings"""
        headings = []
        for i in range(1, 4):
            h_tags = soup.find_all(f'h{i}')
            for h in h_tags:
                text = h.get_text().strip()
                if text:
                    headings.append({
                        'level': i,
                        'text': text
                    })
        return headings

    def _extract_text_content(self, soup):
        """Extract visible text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_images(self, soup):
        """Extract image URLs"""
        images = []
        img_tags = soup.find_all('img')

        for img in img_tags:
            # Try multiple possible src attributes for lazy loading
            src = (img.get('src') or
                   img.get('data-src') or
                   img.get('data-lazy-src') or
                   img.get('data-original') or
                   img.get('data-url'))
            alt = img.get('alt', '')

            if src:
                images.append({
                    'src': src,
                    'alt': alt
                })

        return images

    def _extract_structured_data(self, soup):
        """Extract JSON-LD structured data"""
        structured_data = []
        json_scripts = soup.find_all('script', type='application/ld+json')

        for script in json_scripts:
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except (json.JSONDecodeError, TypeError):
                continue

        return structured_data

    def _extract_meta_tags(self, soup):
        """Extract meta tags"""
        meta_tags = {}
        meta_elements = soup.find_all('meta')

        for meta in meta_elements:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')

            if name and content:
                meta_tags[name] = content

        return meta_tags
