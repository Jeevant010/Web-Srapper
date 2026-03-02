"""
LangChain document loaders for web content.
"""

from __future__ import annotations

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document


def load_documents(url: str) -> list[Document]:
    """
    Load a web page as LangChain Documents using WebBaseLoader + BS4.

    Args:
        url: The URL to load.

    Returns:
        List of LangChain Document objects.
    """
    loader = WebBaseLoader(
        web_paths=[url],
        bs_kwargs={"parse_only": None},  # load full page
    )
    return loader.load()


def load_from_html(html: str, metadata: dict | None = None) -> list[Document]:
    """
    Create LangChain Documents from raw HTML string.

    Args:
        html: Raw HTML content.
        metadata: Optional metadata to attach.

    Returns:
        List containing a single Document.
    """
    from bs4 import BeautifulSoup
    import html2text

    soup = BeautifulSoup(html, "lxml")

    # Remove noise
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.body_width = 0  # no wrapping
    text = converter.handle(str(soup))

    doc = Document(
        page_content=text.strip(),
        metadata=metadata or {},
    )
    return [doc]
