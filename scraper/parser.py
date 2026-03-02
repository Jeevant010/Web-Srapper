"""
BeautifulSoup-based HTML parser with extraction strategies for
text, links, images, tables, and page metadata.
"""

from __future__ import annotations

from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag


# ─────────────────────────────────────────────────────────
# Core parser
# ─────────────────────────────────────────────────────────

def parse_html(html: str, parser: str = "lxml") -> BeautifulSoup:
    """Parse raw HTML into a BeautifulSoup tree."""
    return BeautifulSoup(html, parser)


# ─────────────────────────────────────────────────────────
# Text extraction
# ─────────────────────────────────────────────────────────

def extract_text(soup: BeautifulSoup, tags: list[str] | None = None) -> str:
    """
    Extract readable text from specific HTML tags.
    If no tags are specified, extracts all visible text.
    """
    if tags:
        parts: list[str] = []
        for tag_name in tags:
            for element in soup.find_all(tag_name):
                text = element.get_text(strip=True)
                if text:
                    parts.append(text)
        return "\n".join(parts)
    else:
        # Remove script and style elements
        for element in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            element.decompose()
        return soup.get_text(separator="\n", strip=True)


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
