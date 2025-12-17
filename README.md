# 🛒 Universal E-commerce Parser

## 📌 Overview

This project is a **universal e-commerce parser** with web interface and AI-powered URL filtering.

**Input:**
- Website URL (e.g. `https://atelierhome-art.com`)

**Output:**
- `catalog.csv` containing product data
- Folder with downloaded product images
- Web interface for easy parsing

The parser:
- Automatically reads `sitemap.xml`
- Uses AI to filter product URLs
- Extracts product data from structured data and meta tags
- Downloads product images
- Exports everything to CSV

Works on **any online store** without manual configuration.

---

## 🎯 Data to Extract per Product

For each product page extract:

1. **Title** (from og:title, meta tags, or HTML)
2. **Description** (from og:description, meta tags)
3. **Price** (from meta tags or HTML parsing)
4. **Currency** (auto-detected)
5. **All product images**

### Image naming format

```
1.webp
1-1.webp
1-2.webp
2.webp
2-1.webp
```

---

## 🧠 Core Idea

Multi-level data extraction:

1. **JSON-LD structured data** (Product schema)
2. **Open Graph meta tags** (og:title, og:description, og:image)
3. **HTML content parsing** (fallback for price patterns)
4. **AI-powered URL filtering** (DeepSeek for product page detection)

---

## 🏗 Architecture

```
URL
 ↓
robots.txt → sitemap.xml
 ↓
List of all URLs
 ↓
AI filtering (DeepSeek)
 ↓
Product URLs only
 ↓
HTML fetch
 ↓
Multi-level data extraction
 ↓
Image download
 ↓
CSV export
```

---

## 🧩 Project Structure

```
.
├── main.py
├── config.py
├── requirements.txt
├── README.md
│
├── crawler/
│   ├── sitemap.py
│   ├── fetcher.py
│   └── filters.py
│
├── extractor/
│   ├── raw_content.py
│   └── images.py
│
├── ai/
│   ├── deepseek_client.py
│   └── product_parser.py
│
├── storage/
│   ├── csv_writer.py
│   └── image_store.py
│
└── output/
    ├── images/
    └── catalog.csv
```

---

## ⚙️ Tech Stack

- **Python 3.11+**
- **Playwright** (page rendering)
- **BeautifulSoup4**
- **DeepSeek API**
- `requests`, `lxml`, `pandas`

---

## 🔑 Configuration

Create `config.py`:

```python
DEEPSEEK_API_KEY = "YOUR_API_KEY"
DEEPSEEK_MODEL = "deepseek-chat"
REQUEST_TIMEOUT = 30
MAX_PAGES = 10000
```

---

## 🌐 Sitemap Processing

### Behavior

1. Check:
   - `/sitemap.xml`
   - `/sitemap_index.xml`
   - `robots.txt`
2. Parse all sitemap URLs
3. Extract all page links

---

## 🌍 Page Fetching

Use **Playwright (Chromium)**.

Requirements:
- Wait for network idle
- Block analytics & ads
- Return full rendered HTML

---

## 📦 Raw Content Extraction

From each page collect:
- `<title>`
- all `<h1–h3>`
- full visible text
- all `<img src>`
- all `<script type="application/ld+json">`

---

## 🧠 AI Product Extraction

Strict JSON response:

```json
{
  "is_product": true,
  "title": "",
  "description": "",
  "price": "",
  "old_price": "",
  "currency": "",
  "confidence": 0.0
}
```

---

## 🖼 Image Handling

- Filter icons, svg, trackers
- Prefer large images
- Preserve original format

---

## 📄 CSV Output

Columns:

```csv
id,url,title,description,price,old_price,currency,images
```

---

## 🚀 How to Run

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
playwright install

# Configure API key
cp .env.example .env
# Edit .env with your DeepSeek API key

# Run web interface
python web.py

# Or run CLI parser
python main.py https://example.com
```

Open http://localhost:5000 for web interface.

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t shop-parser .
docker run -p 5000:5000 -v $(pwd)/output:/app/output shop-parser
```

### Production Deployment

1. Set environment variables:
```bash
export DEEPSEEK_API_KEY="your_key_here"
export FLASK_ENV=production
```

2. Use reverse proxy (nginx) for production
3. Set up SSL certificates
4. Configure monitoring and logging

---

## 📈 Future Improvements

- Async processing
- UI dashboard
- Export to CMS
- SaaS deployment

---

## ✅ Goal

A fully universal AI-based e-commerce parser.

Claude Code should implement all modules accordingly.
