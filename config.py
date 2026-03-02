"""
Centralised configuration for the Web Scraper pipeline.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── HTTP Settings ───────────────────────────────────────
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = 3

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── LangChain Settings ──────────────────────────────────
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200
DEFAULT_TAGS = ["p", "h1", "h2", "h3", "h4", "li", "a", "span", "div"]

# ── LLM Model Names ────────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
