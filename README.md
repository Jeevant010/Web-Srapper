# 🕸️ Web Scraper Pipeline — LangChain + BeautifulSoup

A modular, production-grade web scraper built with **LangChain** and **BeautifulSoup4** for Python 3.13. Scrape any webpage and extract text, links, images, tables, and metadata — then optionally use **Gemini** or **Groq** LLMs to summarize content or answer questions about it.

---

## ⚡ Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Jeevant010/Web-Srapper.git
cd Web-Srapper

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up API keys (optional — needed for AI features)
copy .env.example .env
# Edit .env and add your GOOGLE_API_KEY and/or GROQ_API_KEY

# 5. Run the scraper
python main.py https://quotes.toscrape.com
```

---

## 📦 Architecture

```
Web-Srapper/
├── main.py                  # CLI entrypoint
├── config.py                # Central configuration
├── requirements.txt         # Python dependencies
├── .env.example             # API key template
│
├── scraper/                 # Core scraping layer
│   ├── fetcher.py           #   HTTP fetching with retries
│   └── parser.py            #   BeautifulSoup extraction strategies
│
├── pipeline/                # LangChain AI layer
│   ├── loader.py            #   Document loaders
│   ├── transformer.py       #   BS4 transformer + text splitter
│   └── chains.py            #   LLM chains (Gemini / Groq)
│
├── export/                  # Output layer
│   └── exporter.py          #   JSON, CSV, Markdown export
│
└── output/                  # Generated output files
```

---

## 🚀 Usage

### Basic scrape (no API key needed)

```bash
python main.py https://example.com
```

### Choose export format

```bash
python main.py https://example.com --format json
python main.py https://example.com --format csv
python main.py https://example.com --format md
python main.py https://example.com --format all   # default
```

### AI Summarization

```bash
python main.py https://example.com --summarize --provider gemini
python main.py https://example.com --summarize --provider groq
```

### Ask a question about the page

```bash
python main.py https://example.com --ask "What is the main topic of this page?"
```

### Extract specific HTML tags only

```bash
python main.py https://example.com --tags "p,h1,h2,h3,li"
```

### Full combo

```bash
python main.py https://quotes.toscrape.com \
    --output-dir ./results \
    --format all \
    --summarize \
    --ask "What quotes are on this page?" \
    --provider gemini \
    --tags "p,h1,span"
```

---

## 🛠️ CLI Reference

| Argument | Default | Description |
|---|---|---|
| `url` | *(required)* | URL to scrape |
| `--output-dir` | `./output` | Output directory |
| `--format` | `all` | `json`, `csv`, `md`, or `all` |
| `--summarize` | `false` | Run LLM summarization |
| `--ask` | — | Ask a question about the content |
| `--provider` | `gemini` | LLM provider: `gemini` or `groq` |
| `--tags` | — | Comma-separated HTML tags to extract |

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | For Gemini | Google AI / Gemini API key |
| `GROQ_API_KEY` | For Groq | Groq API key |
| `USER_AGENT` | No | Custom User-Agent string |
| `REQUEST_TIMEOUT` | No | HTTP timeout in seconds (default: 30) |

> **Note:** The core scraping works without any API keys. Keys are only needed for `--summarize` and `--ask` features.

---

## 📊 Output Files

After running, the `output/` directory contains:

| File | Description |
|---|---|
| `scraped_data.json` | Full structured data (text, links, images, tables, metadata) |
| `scraped_data.md` | Human-readable Markdown report |
| `scraped_data_links.csv` | All extracted links |
| `scraped_data_images.csv` | All extracted images |
| `scraped_data_table_N.csv` | Each table as a separate CSV |

---

## 🧩 What Gets Extracted

1. **Text** — Readable content from configured HTML tags
2. **Links** — All `<a>` tags with text, absolute URL, and title
3. **Images** — All `<img>` tags with src (including lazy-loaded), alt, dimensions
4. **Tables** — Every `<table>` as structured rows/columns
5. **Metadata** — Title, meta description, canonical URL, Open Graph tags, language

---

## 📋 Requirements

- **Python** 3.13+
- All dependencies listed in `requirements.txt`

---

## 📝 License

See [LICENSE](./LICENSE) for details.