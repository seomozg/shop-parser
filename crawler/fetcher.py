from playwright.sync_api import sync_playwright
import config

class PageFetcher:
    """Fetches page content using Playwright"""

    def __init__(self):
        self.playwright = None
        self.browser = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        # Use system Chromium with new headless mode
        self.browser = self.playwright.chromium.launch(
            executable_path="/usr/bin/chromium",  # System Chromium path
            args=[
                '--headless=new',  # Use new headless mode
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_page(self, url):
        """Fetch page content with full rendering"""
        try:
            page = self.browser.new_page()

            # Block analytics and ads for faster loading
            page.route("**/*", lambda route: route.abort() if any(
                pattern in route.request.url for pattern in [
                    "google-analytics.com", "googletagmanager.com",
                    "facebook.com/tr", "doubleclick.net", "hotjar.com"
                ]
            ) else route.continue_())

            # Navigate and wait for DOM content loaded
            page.goto(url, wait_until="domcontentloaded", timeout=config.REQUEST_TIMEOUT * 1000)

            # Get full HTML content
            html_content = page.content()

            page.close()
            return html_content

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
