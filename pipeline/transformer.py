"""
LangChain document transformers — tag extraction & text splitting.
"""

from __future__ import annotations

from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from config import CHUNK_SIZE, CHUNK_OVERLAP, DEFAULT_TAGS


def transform_documents(
    docs: list[Document],
    tags: list[str] | None = None,
) -> list[Document]:
    """
    Use BeautifulSoupTransformer to extract content from specific HTML tags.

    Args:
        docs: Documents whose page_content is HTML.
        tags: HTML tags to keep (default from config).

    Returns:
        Transformed documents with only the specified tag content.
    """
    bs_transformer = BeautifulSoupTransformer()
    return bs_transformer.transform_documents(
        docs,
        tags_to_extract=tags or DEFAULT_TAGS,
    )


def split_documents(
    docs: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """
    Split documents into smaller chunks for LLM processing.

    Args:
        docs: Documents to split.
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlapping characters between chunks.

    Returns:
        List of smaller Document chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or CHUNK_SIZE,
        chunk_overlap=chunk_overlap or CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)
