import openai
import json
import config

class DeepSeekClient:
    """Client for interacting with DeepSeek AI API"""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        self.model = config.DEEPSEEK_MODEL

    def extract_product_data(self, raw_content, page_url):
        """Extract product data from raw page content using DeepSeek AI"""
        if not raw_content:
            return None

        print(f"DEBUG: Calling DeepSeek AI for URL: {page_url}")
        prompt = self._build_prompt(raw_content, page_url)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting product information from e-commerce websites. Analyze the provided page content and extract product details in strict JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1500  # Increased for images
            )

            result_text = response.choices[0].message.content
            if not result_text:
                print("DEBUG: AI returned empty response")
                return None
            result_text = result_text.strip()
            print(f"DEBUG: AI response: {result_text[:200]}...")

            # Parse JSON response
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            result = json.loads(result_text.strip())
            print(f"DEBUG: Parsed AI result: is_product={result.get('is_product', False)}")

            # Validate required fields
            if not isinstance(result, dict):
                return None

            # Ensure required fields are present
            result.setdefault('is_product', False)
            result.setdefault('title', '')
            result.setdefault('description', '')
            result.setdefault('price', '')
            result.setdefault('old_price', '')
            result.setdefault('currency', '')
            result.setdefault('images', [])

            return result

        except Exception as e:
            print(f"Error extracting product data: {e}")
            return None

    def _build_prompt(self, raw_content, page_url):
        """Build the prompt for the AI"""
        prompt_parts = [
            f"URL: {page_url}",
            "",
            "PAGE CONTENT:"
        ]

        if raw_content.get('title'):
            prompt_parts.append(f"Title: {raw_content['title']}")

        if raw_content.get('headings'):
            prompt_parts.append("Headings:")
            for heading in raw_content['headings'][:5]:  # Limit to first 5 headings
                prompt_parts.append(f"  H{heading['level']}: {heading['text']}")

        if raw_content.get('text_content'):
            # Truncate text content if too long
            text = raw_content['text_content'][:1500]  # Reduced to fit images
            prompt_parts.append(f"Text Content: {text}...")

        if raw_content.get('images'):
            prompt_parts.append("Images found on page:")
            for i, img in enumerate(raw_content['images'][:10]):  # Limit to 10 images
                prompt_parts.append(f"  {i+1}. {img['src']} (alt: {img.get('alt', 'N/A')})")

        if raw_content.get('structured_data'):
            prompt_parts.append("Structured Data:")
            for data in raw_content['structured_data'][:3]:  # Limit to 3 structured data blocks
                if isinstance(data, dict) and data.get('@type') in ['Product', 'Offer', 'AggregateOffer']:
                    prompt_parts.append(f"  {json.dumps(data, indent=2)[:500]}...")

        prompt_parts.extend([
            "",
            "INSTRUCTIONS:",
            "Determine if this page contains a product for sale.",
            "If it's a product page, extract the following information:",
            "- title: Product name",
            "- description: Product description",
            "- price: Current price (numeric only, no currency symbols)",
            "- old_price: Original/compare at price (if different from current price)",
            "- currency: Currency code (e.g., USD, EUR, GBP)",
            "- images: List of 1-5 most relevant product image URLs from the Images found section (prefer larger images, avoid icons/logos)",
            "",
            "Return ONLY valid JSON in this exact format:",
            "{",
            '  "is_product": true|false,',
            '  "title": "product name",',
            '  "description": "product description",',
            '  "price": "123.45",',
            '  "old_price": "150.00",',
            '  "currency": "USD",',
            '  "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]',
            "}"
        ])

        return "\n".join(prompt_parts)
