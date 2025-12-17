from flask import Flask, request, render_template_string, jsonify, send_from_directory, send_file
import os
import sys
import threading
import time
import requests
import json
from urllib.parse import urlparse

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

app = Flask(__name__)

# Global variables for tracking parsing status
parsing_status = {
    'is_running': False,
    'current_url': None,
    'progress': 0,
    'total_pages': 0,
    'found_products': 0,
    'message': '',
    'results': None
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal E-commerce Parser</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #34495e;
        }
        input[type="url"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input[type="url"]:focus {
            border-color: #3498db;
            outline: none;
        }
        button {
            background-color: #3498db;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        button:disabled {
            background-color: #bdc3c7;
            cursor: not-allowed;
        }
        .status {
            margin-top: 30px;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 5px;
            display: none;
        }
        .status.show {
            display: block;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background-color: #3498db;
            width: 0%;
            transition: width 0.3s ease;
        }
        .results {
            margin-top: 30px;
            display: none;
        }
        .results.show {
            display: block;
        }
        .product {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            background-color: #fafafa;
        }
        .product h3 {
            margin: 0 0 10px 0;
            color: #2c3e50;
        }
        .product p {
            margin: 5px 0;
            color: #7f8c8d;
        }
        .download-links {
            margin-top: 20px;
            text-align: center;
        }
        .download-links a {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 20px;
            background-color: #27ae60;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
        .download-links a:hover {
            background-color: #219a52;
        }
        .error {
            color: #e74c3c;
            background-color: #fdf2f2;
            border: 1px solid #f5c6cb;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛒 Universal E-commerce Parser</h1>

        <form id="parserForm">
            <div class="form-group">
                <label for="websiteUrl">URL веб-сайта:</label>
                <input type="url" id="websiteUrl" name="url" placeholder="https://example-shop.com" required>
            </div>
            <button type="submit" id="startButton">Шаг 1: Фильтрация товаров</button>
        </form>

        <div id="productParsingSection" style="display: none; margin-top: 20px;">
            <h3>Шаг 2: Парсинг товаров</h3>
            <button id="startProductParsingButton">Начать парсинг товаров</button>
        </div>

        <div class="status" id="status">
            <h3>Статус парсинга:</h3>
            <p id="statusMessage">Подготовка...</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <p id="progressText">0 / 0 страниц обработано, найдено 0 товаров</p>
        </div>

        <div class="results" id="results">
            <h3>Результаты:</h3>
            <div id="productsList"></div>
            <div class="download-links" id="downloadLinks">
                <a href="/download/csv" download>Скачать CSV</a>
                <a href="/download/images" download>Скачать изображения (ZIP)</a>
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('parserForm');
        const startButton = document.getElementById('startButton');
        const status = document.getElementById('status');
        const results = document.getElementById('results');
        const statusMessage = document.getElementById('statusMessage');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const productsList = document.getElementById('productsList');

        let statusCheckInterval;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = document.getElementById('websiteUrl').value;

            startButton.disabled = true;
            startButton.textContent = 'Запуск...';

            try {
                const response = await fetch('/start_parsing', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (data.success) {
                    status.classList.add('show');
                    results.classList.remove('show');
                    startStatusChecking();
                } else {
                    alert('Ошибка: ' + data.message);
                    startButton.disabled = false;
                    startButton.textContent = 'Начать парсинг';
                }
            } catch (error) {
                alert('Ошибка сети: ' + error.message);
                startButton.disabled = false;
                startButton.textContent = 'Начать парсинг';
            }
        });

        function startStatusChecking() {
            statusCheckInterval = setInterval(async () => {
                try {
                    const response = await fetch('/status');
                    const data = await response.json();

                    statusMessage.textContent = data.message;
                    progressFill.style.width = data.progress + '%';
                    progressText.textContent = `${data.progress.toFixed(1)}% завершено, найдено ${data.found_products} товаров`;

                    if (!data.is_running) {
                        clearInterval(statusCheckInterval);
                        startButton.disabled = false;
                        startButton.textContent = 'Шаг 1: Фильтрация товаров';

                        // Check if filtering is complete and show product parsing button
                        if (data.message && data.message.includes('Готово к парсингу')) {
                            document.getElementById('productParsingSection').style.display = 'block';
                        }

                        if (data.results) {
                            displayResults(data.results);
                        }
                    }
                } catch (error) {
                    console.error('Error checking status:', error);
                }
            }, 1000);
        }

        // Add event listener for product parsing button
        document.getElementById('startProductParsingButton').addEventListener('click', async () => {
            const button = document.getElementById('startProductParsingButton');
            button.disabled = true;
            button.textContent = 'Запуск парсинга товаров...';

            try {
                const response = await fetch('/start_product_parsing', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                const data = await response.json();

                if (data.success) {
                    status.classList.add('show');
                    results.classList.remove('show');
                    startStatusChecking();
                } else {
                    alert('Ошибка: ' + data.message);
                    button.disabled = false;
                    button.textContent = 'Начать парсинг товаров';
                }
            } catch (error) {
                alert('Ошибка сети: ' + error.message);
                button.disabled = false;
                button.textContent = 'Начать парсинг товаров';
            }
        });

        function displayResults(results) {
            productsList.innerHTML = '';

            // Show total count info
            const totalCount = results.total_count || 0;
            if (totalCount > 0) {
                const summaryDiv = document.createElement('div');
                summaryDiv.className = 'product';
                summaryDiv.style.backgroundColor = '#e8f5e8';
                summaryDiv.style.borderColor = '#27ae60';
                summaryDiv.innerHTML = `
                    <h3>✅ Парсинг завершен!</h3>
                    <p><strong>Всего найдено товаров:</strong> ${totalCount}</p>
                    <p><strong>Показаны первые товары:</strong> ${results.products ? results.products.length : 0}</p>
                    <p><small>Полный каталог сохранен в output/catalog.csv</small></p>
                `;
                productsList.appendChild(summaryDiv);
            }

            if (results.products && results.products.length > 0) {
                results.products.forEach(product => {
                    const productDiv = document.createElement('div');
                    productDiv.className = 'product';
                    productDiv.innerHTML = `
                        <h3>${product.title || 'Без названия'}</h3>
                        <p><strong>Цена:</strong> ${product.price || 'N/A'} ${product.currency || ''}</p>
                        <p><strong>Описание:</strong> ${product.description ? product.description.substring(0, 100) + '...' : 'N/A'}</p>
                        <p><strong>Изображений:</strong> ${product.images ? product.images.length : 0}</p>
                        <p><strong>URL:</strong> <a href="${product.url}" target="_blank">${product.url}</a></p>
                    `;
                    productsList.appendChild(productDiv);
                });
            } else if (totalCount === 0) {
                productsList.innerHTML += '<p class="error">Товары не найдены на этом сайте.</p>';
            }

            document.getElementById('results').classList.add('show');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start_parsing', methods=['POST'])
def start_parsing():
    global parsing_status

    if parsing_status['is_running']:
        return jsonify({'success': False, 'message': 'Парсинг уже выполняется'})

    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'success': False, 'message': 'URL не указан'})

    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL")
    except Exception:
        return jsonify({'success': False, 'message': 'Неверный формат URL'})

    # AI is always used for parsing

    # Reset status
    parsing_status = {
        'is_running': True,
        'current_url': url,
        'progress': 0,
        'total_pages': 0,
        'found_products': 0,
        'message': 'Запуск парсинга...',
        'results': None
    }

    # Start parsing in background thread
    thread = threading.Thread(target=run_parsing, args=(url,))
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': 'Парсинг запущен'})

@app.route('/status')
def get_status():
    global parsing_status
    return jsonify(parsing_status)

@app.route('/download/csv')
def download_csv():
    try:
        return send_from_directory('output', 'catalog.csv', as_attachment=True)
    except Exception as e:
        return f"Ошибка: {str(e)}", 404

@app.route('/filter_products', methods=['POST'])
def filter_products():
    """Filter product URLs from the list using AI"""
    data = request.get_json()
    urls = data.get('urls', [])

    if not urls:
        return jsonify({'success': False, 'message': 'URLs not provided'})

    # Use AI to filter product URLs
    from ai.deepseek_client import DeepSeekClient
    ai_client = DeepSeekClient()

    # Prepare prompt with URL list
    url_list = '\n'.join([f'{i+1}. {url}' for i, url in enumerate(urls[:200])])  # Limit to 200 for token limit
    if len(urls) > 200:
        url_list += f'\n... and {len(urls) - 200} more URLs'

    prompt = f"""
You are an expert at identifying product pages on e-commerce websites.

Given the following list of URLs from a sitemap, identify which ones are likely PRODUCT pages (individual items for sale) and return ONLY those URLs.

Exclude:
- Homepage (/)
- Collection/category pages (/collections/)
- Static pages (/pages/)
- Blog pages (/blogs/)
- Any other non-product pages

Return ONLY a list of product URLs, one URL per line, without quotes or brackets. Like:
https://example.com/products/item1
https://example.com/products/item2

URL LIST:
{url_list}
"""

    try:
        response = ai_client.client.chat.completions.create(
            model=ai_client.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that filters product URLs from a list. Return only valid JSON arrays."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content
        if result_text:
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            import json
            product_urls = json.loads(result_text.strip())
        else:
            product_urls = []

        return jsonify({
            'success': True,
            'total_urls': len(urls),
            'product_urls': product_urls,
            'product_count': len(product_urls)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'AI filtering failed: {str(e)}'})

@app.route('/start_product_parsing', methods=['POST'])
def start_product_parsing():
    """Start parsing products from filtered URLs"""
    global parsing_status

    if parsing_status['is_running']:
        return jsonify({'success': False, 'message': 'Парсинг уже выполняется'})

    # Check if filtered URLs file exists
    filtered_urls_file = 'output/filtered_product_urls.txt'
    if not os.path.exists(filtered_urls_file):
        return jsonify({'success': False, 'message': 'Файл с отфильтрованными URL не найден. Сначала выполните фильтрацию.'})

    # Reset status
    parsing_status = {
        'is_running': True,
        'current_url': None,
        'progress': 0,
        'total_pages': 0,
        'found_products': 0,
        'message': 'Запуск парсинга товаров...',
        'results': None
    }

    # Start parsing in background thread
    thread = threading.Thread(target=run_product_parsing)
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': 'Парсинг товаров запущен'})

@app.route('/download/images')
def download_images():
    """Create and download ZIP archive of all images"""
    import zipfile
    import io

    images_dir = 'output/images'
    if not os.path.exists(images_dir):
        return "Изображения не найдены", 404

    # Get all image files
    image_files = []
    for file in os.listdir(images_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
            image_files.append(file)

    if not image_files:
        return "Изображения не найдены", 404

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for image_file in image_files:
            file_path = os.path.join(images_dir, image_file)
            zip_file.write(file_path, image_file)

    zip_buffer.seek(0)

    # Return ZIP file
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='product_images.zip'
    )

def run_product_parsing():
    """Parse products from filtered URLs file"""
    global parsing_status

    try:
        # Read filtered URLs
        filtered_urls_file = 'output/filtered_product_urls.txt'
        with open(filtered_urls_file, 'r', encoding='utf-8') as f:
            filtered_urls = [line.strip() for line in f if line.strip()]

        parsing_status['total_pages'] = len(filtered_urls)
        parsing_status['message'] = f'Начинаем парсинг {len(filtered_urls)} товаров...'

        # Initialize components
        content_extractor = RawContentExtractor()
        product_parser = ProductParser("")  # Will be updated per URL
        csv_writer = CSVWriter("output")
        image_store = ImageStore("output")

        # Process pages
        products = []

        with PageFetcher() as fetcher:
            for i, url in enumerate(filtered_urls, 1):
                parsing_status['progress'] = (i / len(filtered_urls)) * 100
                parsing_status['message'] = f'Обработка {i}/{len(filtered_urls)}: {url[:50]}...'

                try:
                    # Fetch page content
                    html_content = fetcher.fetch_page(url)
                    if not html_content:
                        continue

                    # Extract raw content
                    raw_content = content_extractor.extract_content(html_content)
                    if not raw_content:
                        continue

                    # Parse product data (TEMP mode returns None)
                    product_data = product_parser.parse_product_page(raw_content, url)
                    if product_data:
                        # Add product ID
                        product_data['id'] = str(len(products) + 1)

                        # Download images
                        downloaded_images = product_parser.download_product_images(
                            product_data, "output", product_data['id']
                        )

                        # Update product data with downloaded image filenames
                        product_data['images'] = downloaded_images

                        products.append(product_data)
                        parsing_status['found_products'] = len(products)
                    else:
                        # TEMP mode - still count as processed
                        parsing_status['found_products'] = i  # Show progress

                except Exception as e:
                    print(f"Error processing {url}: {e}")
                    continue

        # Save results
        if products:
            parsing_status['message'] = f'Сохранение {len(products)} товаров...'
            csv_writer.write_products(products)

            # Show first 10 successfully parsed products in UI
            display_products = products[:10]
            parsing_status['results'] = {
                'products': display_products,
                'total_count': len(products),
                'csv_path': 'output/catalog.csv',
                'images_dir': 'output/images'
            }
            parsing_status['message'] = f'Парсинг завершен! Найдено {len(products)} товаров'
        else:
            parsing_status['message'] = 'Товары не найдены'
            parsing_status['results'] = {'products': [], 'total_count': 0}

    except Exception as e:
        parsing_status['message'] = f'Ошибка: {str(e)}'
        parsing_status['results'] = None
    finally:
        parsing_status['is_running'] = False

def run_parsing(website_url):
    """Run the parsing process in background"""
    global parsing_status

    try:
        # Initialize components
        sitemap_parser = SitemapParser(website_url)
        url_filter = URLFilter(website_url)
        content_extractor = RawContentExtractor()
        product_parser = ProductParser(website_url)
        csv_writer = CSVWriter("output")
        image_store = ImageStore("output")

        # Get all URLs from sitemap
        parsing_status['message'] = 'Получение карты сайта...'
        all_urls = sitemap_parser.get_all_urls()
        print(f"DEBUG: Found {len(all_urls)} URLs in sitemap")
        if all_urls:
            print(f"DEBUG: Sample URLs: {all_urls[:3]}")
        parsing_status['message'] = f'Найдено {len(all_urls)} URL в карте сайта'

        # Skip URLFilter - we'll use AI to identify product pages directly from all URLs
        parsing_status['message'] = f'Получено {len(all_urls)} URL из sitemap'
        filtered_urls = []

        # Save URLs to file and use AI to filter all at once
        if all_urls:
            parsing_status['message'] = f'Сохранение {len(all_urls)} URL в файл...'
            try:
                # Save URLs to file
                urls_file = 'output/all_urls.txt'
                with open(urls_file, 'w', encoding='utf-8') as f:
                    for url in all_urls:
                        f.write(url + '\n')

                parsing_status['message'] = f'AI анализ файла с {len(all_urls)} URL...'
                # Use AI to filter all URLs at once by sending file content
                from ai.deepseek_client import DeepSeekClient
                ai_client = DeepSeekClient()

                # Read file content for prompt
                with open(urls_file, 'r', encoding='utf-8') as f:
                    urls_content = f.read()

                # Truncate if too long (keep first 200 URLs for token limit)
                urls_lines = urls_content.split('\n')[:200]
                urls_content = '\n'.join(urls_lines)
                if len(all_urls) > 200:
                    urls_content += f'\n... and {len(all_urls) - 200} more URLs'

                prompt = f"""
You are an expert at identifying product pages on e-commerce websites.

Given the following list of URLs from a sitemap (one URL per line), identify which ones are likely PRODUCT pages (individual items for sale) and return ONLY those URLs.

Exclude:
- Homepage (/)
- Collection/category pages (/collections/)
- Static pages (/pages/)
- Blog pages (/blogs/)
- Any other non-product pages

Return ONLY a JSON array of product URLs, like: ["https://example.com/products/item1", "https://example.com/products/item2"]

URL LIST:
{urls_content}
"""

                response = ai_client.client.chat.completions.create(
                    model=ai_client.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that filters product URLs from a list. Return only valid JSON arrays."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=4000,
                    timeout=600  # 10 minutes timeout
                )

                result_text = response.choices[0].message.content
                if result_text:
                    result_text = result_text.strip()
                    if result_text.startswith('```'):
                        lines = result_text.split('\n')
                        if lines[0].startswith('```'):
                            result_text = '\n'.join(lines[1:])
                        if result_text.endswith('```'):
                            result_text = result_text[:-3].strip()

                    # Try to parse as JSON first, then as plain text
                    try:
                        filtered_urls = json.loads(result_text.strip())
                        # Clean up URLs if they have quotes
                        filtered_urls = [url.strip().strip('"').strip("'") for url in filtered_urls if url and 'https://' in url]
                    except json.JSONDecodeError:
                        # Parse as plain text - one URL per line
                        filtered_urls = [line.strip().strip('"').strip("'").strip(',') for line in result_text.split('\n') if line.strip() and not line.startswith('URL LIST') and 'https://' in line]
                else:
                    filtered_urls = []
                print(f"AI FILTERED: {len(filtered_urls)} product URLs from {len(all_urls)} total")
                print(f"Sample product URLs: {filtered_urls[:5]}")
                parsing_status['total_pages'] = len(filtered_urls)
                parsing_status['message'] = f'AI отфильтровал {len(filtered_urls)} товарных страниц'

                # Save filtered URLs for later parsing
                with open('output/filtered_product_urls.txt', 'w', encoding='utf-8') as f:
                    for url in filtered_urls:
                        f.write(url + '\n')

                parsing_status['message'] = f'Фильтрация завершена! Найдено {len(filtered_urls)} товарных страниц. Готово к парсингу.'
                parsing_status['is_running'] = False
                return

            except Exception as e:
                print(f"AI filtering error: {e}")
                filtered_urls = []

        # Product parsing removed - use separate endpoint

    except Exception as e:
        parsing_status['message'] = f'Ошибка: {str(e)}'
        parsing_status['results'] = None
    finally:
        parsing_status['is_running'] = False

if __name__ == '__main__':
    print("Starting web interface...")
    print("Open http://localhost:5000 in your browser")

    # Check for required environment variables
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("WARNING: DEEPSEEK_API_KEY not set. URL filtering will not work.")
        print("Set it in .env file or environment variables.")

    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
