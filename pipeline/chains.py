"""
LangChain LLM chains for summarization and Q&A over scraped content.
Supports Gemini (Google) and Groq providers.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from rich.console import Console

from config import GOOGLE_API_KEY, GROQ_API_KEY, GEMINI_MODEL, GROQ_MODEL

console = Console()


# ─────────────────────────────────────────────────────────
# LLM factory
# ─────────────────────────────────────────────────────────

def get_llm(provider: str = "gemini") -> BaseChatModel:
    """
    Return an LLM instance based on the chosen provider.

    Args:
        provider: "gemini" or "groq".

    Returns:
        A LangChain chat model.

    Raises:
        ValueError: If no valid API key is found for the provider.
    """
    provider = provider.lower().strip()

    if provider == "gemini":
        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY is not set. Add it to your .env file."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
        )

    elif provider == "groq":
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.3,
        )

    else:
        raise ValueError(f"Unknown provider '{provider}'. Use 'gemini' or 'groq'.")


def _has_any_key() -> bool:
    """Check if at least one LLM API key is available."""
    return bool(GOOGLE_API_KEY or GROQ_API_KEY)


# ─────────────────────────────────────────────────────────
# Summarization
# ─────────────────────────────────────────────────────────

SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant that produces clear, concise summaries "
        "of web page content. Preserve key facts and structure.",
    ),
    (
        "human",
        "Summarize the following web page content in a well-structured format:\n\n"
        "{text}",
    ),
])


def summarize_documents(docs: list[Document], provider: str = "gemini") -> str:
    """
    Summarize a list of documents using an LLM.

    Falls back to returning the first 2000 chars of raw text if no API key
    is configured.

    Args:
        docs: Documents to summarize.
        provider: LLM provider ("gemini" or "groq").

    Returns:
        Summary string.
    """
    if not _has_any_key():
        console.print("[yellow]⚠ No API key set — returning raw text preview.[/yellow]")
        combined = "\n\n".join(d.page_content for d in docs)
        return combined[:2000] + ("\n…(truncated)" if len(combined) > 2000 else "")

    try:
        llm = get_llm(provider)
        combined = "\n\n".join(d.page_content for d in docs)

        # Truncate to avoid token limits
        max_chars = 30_000
        if len(combined) > max_chars:
            combined = combined[:max_chars] + "\n…(content truncated for LLM)"

        chain = SUMMARIZE_PROMPT | llm
        result = chain.invoke({"text": combined})
        return result.content

    except Exception as exc:
        console.print(f"[red]✗ Summarization failed:[/red] {exc}")
        combined = "\n\n".join(d.page_content for d in docs)
        return combined[:2000] + "\n…(truncated — LLM error occurred)"


# ─────────────────────────────────────────────────────────
# Q&A
# ─────────────────────────────────────────────────────────

QA_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful assistant. Answer the user's question based ONLY "
        "on the provided web page content. If the answer is not in the "
        "content, say so clearly.",
    ),
    (
        "human",
        "Web page content:\n\n{context}\n\n---\n\nQuestion: {question}",
    ),
])


def qa_over_documents(
    docs: list[Document],
    question: str,
    provider: str = "gemini",
) -> str:
    """
    Answer a question using the scraped document content.

    Args:
        docs: Documents providing context.
        question: The user's question.
        provider: LLM provider ("gemini" or "groq").

    Returns:
        Answer string.
    """
    if not _has_any_key():
        return "⚠ No API key configured. Cannot perform Q&A."

    try:
        llm = get_llm(provider)
        combined = "\n\n".join(d.page_content for d in docs)

        max_chars = 30_000
        if len(combined) > max_chars:
            combined = combined[:max_chars] + "\n…(content truncated)"

        chain = QA_PROMPT | llm
        result = chain.invoke({"context": combined, "question": question})
        return result.content

    except Exception as exc:
        return f"✗ Q&A failed: {exc}"
