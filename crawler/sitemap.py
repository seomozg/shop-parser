import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import urljoin, urlparse
import config
import warnings
from xml.etree import ElementTree as ET
import html

# Suppress XML parsing warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

class SitemapParser:
    """Parses sitemap.xml and robots.txt to extract page URLs"""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def get_all_urls(self):
        """Get all URLs from sitemap and robots.txt"""
        urls = set()

        # Try sitemap location
        sitemap_locations = [
            '/sitemap.xml'
        ]

        for sitemap_path in sitemap_locations:
            sitemap_url = f"{self.base_url}{sitemap_path}"
            print(f"DEBUG: Trying sitemap location: {sitemap_path}")
            sitemap_urls = self._parse_sitemap_url(sitemap_url)
            if sitemap_urls:
                print(f"DEBUG: Sitemap {sitemap_path} returned {len(sitemap_urls)} URLs")
                urls.update(sitemap_urls)
                # Don't break, try all locations

        # Try robots.txt for additional sitemaps
        robots_urls = self._parse_robots_txt()
        urls.update(robots_urls)

        # Only use sitemap URLs

        print(f"DEBUG: Total unique URLs found: {len(urls)}")
        # Show sample URLs by type
        sample_urls = list(urls)[:10]
        for i, url in enumerate(sample_urls):
            print(f"DEBUG: Sample URL {i+1}: {url}")

        return list(urls)

    def _parse_sitemap_url(self, sitemap_url):
        """Parse a specific sitemap URL"""
        urls = set()
        print(f"DEBUG: Fetching sitemap from: {sitemap_url}")

        try:
            response = self.session.get(sitemap_url, timeout=10)
            print(f"DEBUG: Sitemap response status: {response.status_code}")
            if response.status_code != 200:
                print(f"DEBUG: Non-200 status code, skipping")
                return urls

            content_length = len(response.content)
            print(f"DEBUG: Sitemap content length: {content_length} bytes")
            print(f"DEBUG: Content preview: {response.text[:500]}...")

            # Try ElementTree XML parser first
            try:
                root = ET.fromstring(response.content)
                print("DEBUG: Successfully parsed as XML with ElementTree")

                # Check for XML namespaces - use full namespace URI
                sitemap_elements = root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap')
                if sitemap_elements:
                    print(f"DEBUG: Found sitemap index with {len(sitemap_elements)} sitemaps")
                    for i, sitemap_elem in enumerate(sitemap_elements):
                        loc = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        print(f"DEBUG: Sitemap elem {i+1}, loc found: {loc is not None}, text: {loc.text if loc else None}")
                        if loc is not None and loc.text:
                            sub_sitemap_url = html.unescape(loc.text.strip())
                            print(f"DEBUG: Parsing sub-sitemap {i+1}: {sub_sitemap_url}")
                            sub_sitemap_urls = self._parse_sitemap_url(sub_sitemap_url)
                            print(f"DEBUG: Sub-sitemap {i+1} returned {len(sub_sitemap_urls)} URLs")
                            urls.update(sub_sitemap_urls)
                    print(f"DEBUG: Total URLs from all sub-sitemaps: {len(urls)}")
                    return urls

                # Find URL elements
                url_elements = root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url') or root.findall('url')
                print(f"DEBUG: Found {len(url_elements)} <url> elements")

                for i, url_elem in enumerate(url_elements):
                    loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None and loc.text:
                        url = loc.text.strip()
                        if i < 5:
                            print(f"DEBUG: URL {i+1}: {url}")
                        urls.add(url)

                if len(url_elements) > 10:
                    print(f"DEBUG: ... and {len(url_elements) - 10} more URLs")

            except ET.ParseError as e:
                print(f"DEBUG: ElementTree XML parsing failed: {e}, trying BeautifulSoup XML")
                # Fallback to BeautifulSoup with XML parser
                soup = BeautifulSoup(response.content, 'xml')
                print("DEBUG: Using BeautifulSoup XML parser")

                # Check if this is a sitemap index
                sitemap_elements = soup.find_all('sitemap')
                if sitemap_elements:
                    print(f"DEBUG: Found sitemap index with {len(sitemap_elements)} sitemaps")
                    for i, sitemap_elem in enumerate(sitemap_elements):
                        loc = sitemap_elem.find('loc')
                        if loc and loc.text:
                            sub_sitemap_url = loc.text.strip()
                            print(f"DEBUG: Parsing sub-sitemap {i+1}: {sub_sitemap_url}")
                            sub_sitemap_urls = self._parse_sitemap_url(sub_sitemap_url)
                            print(f"DEBUG: Sub-sitemap {i+1} returned {len(sub_sitemap_urls)} URLs")
                            urls.update(sub_sitemap_urls)
                    print(f"DEBUG: Total URLs from all sub-sitemaps: {len(urls)}")
                    return urls

                url_elements = soup.find_all('url')
                print(f"DEBUG: Found {len(url_elements)} <url> elements")

                for i, url_elem in enumerate(url_elements[:10]):
                    loc = url_elem.find('loc')
                    if loc and loc.text:
                        url = loc.text.strip()
                        if i < 5:
                            print(f"DEBUG: URL {i+1}: {url}")
                        urls.add(url)

                if len(url_elements) > 10:
                    print(f"DEBUG: ... and {len(url_elements) - 10} more URLs")

        except Exception as e:
            print(f"DEBUG: Error parsing sitemap {sitemap_url}: {e}")

        return urls

    def _crawl_homepage(self):
        """Basic crawling from homepage to find product pages"""
        urls = set()
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all links on homepage
            links = soup.find_all('a', href=True)
            print(f"DEBUG: Found {len(links)} links on homepage")

            for link in links:
                href = link.get('href')
                if not href or not isinstance(href, str):
                    continue

                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = f"{self.base_url}{href}"
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue

                # Filter to same domain and likely product pages
                try:
                    parsed_full = urlparse(full_url)
                    parsed_base = urlparse(self.base_url)
                    if parsed_full.netloc == parsed_base.netloc:
                        # Look for common product page patterns
                        path = parsed_full.path.lower()
                        if any(pattern in path for pattern in ['/product', '/item', '/p/', '/shop', '/store']):
                            urls.add(full_url)
                            if len(urls) >= 20:  # Limit to 20 URLs
                                break
                except:
                    continue

            print(f"DEBUG: Found {len(urls)} potential product URLs from homepage")

        except Exception as e:
            print(f"DEBUG: Error crawling homepage: {e}")

        return urls

    def _parse_sitemap(self):
        """Parse sitemap.xml"""
        urls = set()
        sitemap_url = f"{self.base_url}/sitemap.xml"

        print(f"DEBUG: Fetching sitemap from: {sitemap_url}")

        try:
            response = self.session.get(sitemap_url)
            print(f"DEBUG: Sitemap response status: {response.status_code}")
            response.raise_for_status()

            content_length = len(response.content)
            print(f"DEBUG: Sitemap content length: {content_length} bytes")

            # Try XML parser first, fallback to HTML parser
            try:
                soup = BeautifulSoup(response.content, 'xml')
                print("DEBUG: Successfully parsed as XML")
            except Exception as e:
                print(f"DEBUG: XML parsing failed, trying HTML parser: {e}")
                soup = BeautifulSoup(response.content, 'html.parser')
                print("DEBUG: Using HTML parser")

            url_elements = soup.find_all('url')
            print(f"DEBUG: Found {len(url_elements)} <url> elements")

            for i, url_elem in enumerate(url_elements[:5]):  # Show first 5
                loc = url_elem.find('loc')
                if loc and loc.text:
                    url = loc.text.strip()
                    print(f"DEBUG: URL {i+1}: {url}")
                    urls.add(url)

            if len(url_elements) > 5:
                print(f"DEBUG: ... and {len(url_elements) - 5} more URLs")

        except Exception as e:
            print(f"Error parsing sitemap.xml: {e}")

        return urls

    def _parse_robots_txt(self):
        """Parse robots.txt for sitemap entries"""
        urls = set()
        robots_url = f"{self.base_url}/robots.txt"

        try:
            response = self.session.get(robots_url)
            response.raise_for_status()

            lines = response.text.split('\n')
            for line in lines:
                line = line.strip()
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line[8:].strip()
                    if sitemap_url:
                        # Parse the sitemap URL
                        sitemap_urls = self._parse_single_sitemap(sitemap_url)
                        urls.update(sitemap_urls)

        except Exception as e:
            print(f"Error parsing robots.txt: {e}")

        return urls

    def _parse_single_sitemap(self, sitemap_url):
        """Parse a single sitemap URL"""
        urls = set()

        try:
            response = self.session.get(sitemap_url)
            response.raise_for_status()

            # Try XML parser first, fallback to HTML parser
            try:
                soup = BeautifulSoup(response.content, 'xml')
            except:
                soup = BeautifulSoup(response.content, 'html.parser')

            url_elements = soup.find_all('url')

            for url_elem in url_elements:
                loc = url_elem.find('loc')
                if loc and loc.text:
                    urls.add(loc.text.strip())

        except Exception as e:
            print(f"Error parsing sitemap {sitemap_url}: {e}")

        return urls
