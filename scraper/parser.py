"""
BeautifulSoup-based HTML parser with extraction strategies for
text, links, images, tables, and page metadata.
"""

from __future__ import annotations

import copy
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag


# ── Patterns used to identify noisy sidebar / nav elements ──
_NOISE_CLASS_PATTERNS = [
    "sidebar", "nav", "menu", "toc", "breadcrumb",
    "related", "share", "social", "comment", "ad-",
    "widget", "footer-", "header-", "cookie",
]

_MAIN_CONTENT_CLASS_RE = re.compile(
    r"article[_-]?body|post[_-]?content|entry[_-]?content|"
    r"article[_-]?content|page[_-]?content|main[_-]?content|"
    r"text[_-]?container|article[_-]?text",
    re.IGNORECASE,
)

_MAIN_CONTENT_ID_RE = re.compile(
    r"article|content|main|post",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────
# Core parser
# ─────────────────────────────────────────────────────────

def parse_html(html: str, parser: str = "lxml") -> BeautifulSoup:
    """Parse raw HTML into a BeautifulSoup tree."""
    return BeautifulSoup(html, parser)


# ─────────────────────────────────────────────────────────
# Text extraction
# ─────────────────────────────────────────────────────────

def _has_noise_class(css_classes: list[str] | str | None) -> bool:
    """Return True if any CSS class matches a known noise pattern."""
    if not css_classes:
        return False
    if isinstance(css_classes, str):
        css_classes = [css_classes]
    joined = " ".join(css_classes).lower()
    return any(p in joined for p in _NOISE_CLASS_PATTERNS)


def _strip_noise(work: BeautifulSoup) -> None:
    """Remove script, style, nav, sidebar, and other non-content elements."""
    # Remove noise tags entirely
    for el in work(["script", "style", "noscript", "header", "footer",
                     "nav", "aside", "form", "iframe"]):
        el.decompose()

    # Remove elements whose CSS classes match known noise patterns
    for el in work.find_all(class_=lambda c: _has_noise_class(c)):
        el.decompose()

    # Remove elements with noise-related roles
    for role in ("navigation", "banner", "complementary", "contentinfo"):
        for el in work.find_all(attrs={"role": role}):
            el.decompose()


def _find_main_content(work: BeautifulSoup) -> Tag | None:
    """Try to locate the primary article / content container."""
    # 1. <article> tag (most semantic)
    article = work.find("article")
    if article and len(article.get_text(strip=True)) > 200:
        return article

    # 2. <main> tag
    main = work.find("main")
    if main and len(main.get_text(strip=True)) > 200:
        return main

    # 3. Element with a content-related class name
    by_class = work.find(class_=_MAIN_CONTENT_CLASS_RE)
    if by_class and len(by_class.get_text(strip=True)) > 200:
        return by_class

    # 4. Element with a content-related id
    by_id = work.find(id=_MAIN_CONTENT_ID_RE)
    if by_id and len(by_id.get_text(strip=True)) > 200:
        return by_id

    return None


def extract_text(soup: BeautifulSoup, tags: list[str] | None = None) -> str:
    """
    Extract readable article text from a web page.

    Strategy:
        1. If *tags* are given, extract text only from those HTML tags.
        2. Otherwise, strip noise elements (nav, sidebar, ads, …),
           try to locate the main content container (<article>, <main>,
           or common article-body class), and extract text from there.
        3. Falls back to full-page text (with noise stripped) when no
           main container can be identified.
    """
    if tags:
        parts: list[str] = []
        for tag_name in tags:
            for element in soup.find_all(tag_name):
                text = element.get_text(strip=True)
                if text:
                    parts.append(text)
        return "\n".join(parts)

    # Work on a deep copy so the original soup stays intact
    work = copy.copy(soup)

    # Strip noise elements (sidebar, nav, ads, etc.)
    _strip_noise(work)

    # Try to find the main content container
    main = _find_main_content(work)
    target = main if main else work

    return target.get_text(separator="\n", strip=True)


# ─────────────────────────────────────────────────────────
# Link extraction
# ─────────────────────────────────────────────────────────

def extract_links(soup: BeautifulSoup, base_url: str = "") -> list[dict]:
    """
    Extract all anchor links with text + absolute URL.

    Returns:
        list of {"text": ..., "href": ..., "title": ...}
    """
    links: list[dict] = []
    seen: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if base_url:
            href = urljoin(base_url, href)

        if href in seen or href.startswith(("javascript:", "mailto:", "#")):
            continue
        seen.add(href)

        links.append({
            "text": a_tag.get_text(strip=True) or "[no text]",
            "href": href,
            "title": a_tag.get("title", ""),
        })

    return links


# ─────────────────────────────────────────────────────────
# Image extraction
# ─────────────────────────────────────────────────────────

def extract_images(soup: BeautifulSoup, base_url: str = "") -> list[dict]:
    """
    Extract all image sources with alt text and dimensions.

    Returns:
        list of {"src": ..., "alt": ..., "width": ..., "height": ...}
    """
    images: list[dict] = []

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src:
            # Try data-src (lazy loading)
            src = img.get("data-src", "")
        if not src:
            continue

        if base_url:
            src = urljoin(base_url, src)

        images.append({
            "src": src,
            "alt": img.get("alt", ""),
            "width": img.get("width", ""),
            "height": img.get("height", ""),
        })

    return images


# ─────────────────────────────────────────────────────────
# Table extraction
# ─────────────────────────────────────────────────────────

def extract_tables(soup: BeautifulSoup) -> list[list[list[str]]]:
    """
    Extract all HTML tables as nested lists.

    Returns:
        list of tables, each table is a list of rows,
        each row is a list of cell strings.
    """
    tables: list[list[list[str]]] = []

    for table in soup.find_all("table"):
        rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            row = [cell.get_text(strip=True) for cell in cells]
            if row:
                rows.append(row)
        if rows:
            tables.append(rows)

    return tables


# ─────────────────────────────────────────────────────────
# Metadata extraction
# ─────────────────────────────────────────────────────────

def extract_metadata(soup: BeautifulSoup) -> dict:
    """
    Extract page metadata: title, description, OG tags, canonical URL.
    """
    meta: dict = {}

    # Title
    title_tag = soup.find("title")
    meta["title"] = title_tag.get_text(strip=True) if title_tag else ""

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    meta["description"] = desc_tag["content"] if desc_tag and desc_tag.get("content") else ""

    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    meta["canonical_url"] = canonical["href"] if canonical and canonical.get("href") else ""

    # Open Graph tags
    og: dict[str, str] = {}
    for og_tag in soup.find_all("meta", attrs={"property": lambda v: v and v.startswith("og:")}):
        prop = og_tag["property"]
        content = og_tag.get("content", "")
        og[prop] = content
    meta["og"] = og

    # Language
    html_tag = soup.find("html")
    if html_tag and isinstance(html_tag, Tag):
        meta["language"] = html_tag.get("lang", "")
    else:
        meta["language"] = ""

    return meta
