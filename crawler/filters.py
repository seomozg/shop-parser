from urllib.parse import urlparse
import config

class URLFilter:
    """Filters URLs to keep only relevant pages"""

    def __init__(self, base_url):
        self.base_domain = urlparse(base_url).netloc
        self.base_url = base_url.rstrip('/')

    def filter_urls(self, urls):
        """Filter URLs to keep only relevant pages"""
        filtered_urls = []
        skipped_count = 0

        for url in urls:
            if self._is_valid_url(url):
                filtered_urls.append(url)
            else:
                skipped_count += 1

        print(f"DEBUG: Total URLs: {len(urls)}, Filtered: {len(filtered_urls)}, Skipped: {skipped_count}")

        # Show sample of filtered URLs by path type
        path_counts = {}
        for url in filtered_urls[:100]:  # Sample first 100
            try:
                path = urlparse(url).path
                if '/' in path:
                    path_type = path.split('/')[1] if len(path.split('/')) > 1 else 'root'
                else:
                    path_type = 'root'
                path_counts[path_type] = path_counts.get(path_type, 0) + 1
            except:
                pass

        print(f"DEBUG: Path type counts: {path_counts}")

        # Limit to MAX_PAGES
        return filtered_urls[:config.MAX_PAGES]

    def _is_valid_url(self, url):
        """Check if URL is valid for crawling"""
        try:
            parsed = urlparse(url)

            # Must have same domain
            if parsed.netloc != self.base_domain:
                return False

            # Must be HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False

            # Skip file extensions (images, scripts, etc.)
            path = parsed.path.lower()
            if any(path.endswith(ext) for ext in ['.jpg', '.png', '.gif', '.svg', '.ico', '.css', '.js', '.pdf', '.zip', '.woff', '.woff2', '.ttf', '.eot']):
                return False

            # Skip very specific non-content paths
            skip_patterns = [
                '/cart', '/checkout', '/account', '/login', '/register',
                '/search', '/admin', '/wp-admin', '/api/', '/cdn-',
                '/javascript', '/css', '/images/', '/fonts/', '/assets/',
                '/ajax', '/json', '/xml', '/rss', '/feed'
            ]

            # Skip if matches skip patterns
            for pattern in skip_patterns:
                if pattern in path:
                    return False

            # Allow all other URLs from the same domain (be very permissive for sitemap URLs)
            return True

        except Exception:
            return False
