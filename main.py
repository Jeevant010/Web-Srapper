#!/usr/bin/env python3
"""
Web Scraper Pipeline — LangChain + BeautifulSoup

CLI entrypoint that orchestrates fetching, parsing, LangChain processing,
and exporting of web page data.

Usage:
    python main.py <URL> [OPTIONS]

Examples:
    python main.py https://quotes.toscrape.com
    python main.py https://example.com --format json --summarize --provider gemini
    python main.py https://example.com --ask "What is the main topic?"
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# ── Project imports ──────────────────────────────────────
from scraper.fetcher import fetch_page
from scraper.parser import (
    parse_html,
    extract_text,
    extract_links,
    extract_images,
    extract_tables,
    extract_metadata,
)
from pipeline.loader import load_from_html
from pipeline.transformer import split_documents
from pipeline.chains import summarize_documents, qa_over_documents
from export.exporter import export_json, export_csv, export_markdown

console = Console()


# ─────────────────────────────────────────────────────────
# CLI argument parser
# ─────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="web-scraper",
        description="🕸️  LangChain + BeautifulSoup Web Scraper Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url",
        help="URL of the web page to scrape",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "csv", "md", "all"],
        default="all",
        help="Export format (default: all)",
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Run LLM summarization on the scraped content",
    )
    parser.add_argument(
        "--ask",
        type=str,
        default=None,
        help="Ask a question about the page content",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "groq"],
        default="gemini",
        help="LLM provider for summarization / Q&A (default: gemini)",
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Comma-separated HTML tags to extract (e.g. p,h1,h2,li)",
    )
    return parser


def _slugify(text: str, max_length: int = 60) -> str:
    """Convert a string into a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)   # remove non-word chars
    text = re.sub(r"[\s_]+", "-", text)     # spaces/underscores → hyphens
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_length] or "scraped_page"


# ─────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────

def run(args: argparse.Namespace) -> None:
    url: str = args.url
    output_dir = Path(args.output_dir)
    tags = args.tags.split(",") if args.tags else None

    # ── Banner ────────────────────────────────────────
    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]🕸️  Web Scraper Pipeline[/bold cyan]\n"
            f"[dim]URL:[/dim]  {url}\n"
            f"[dim]Provider:[/dim] {args.provider}  |  "
            f"[dim]Format:[/dim] {args.format}",
            border_style="bright_blue",
        )
    )
    console.print()

    # ── Step 1: Fetch ────────────────────────────────
    console.print("[bold]① Fetching page…[/bold]")
    response = fetch_page(url)
    html = response.text
    console.print()

    # ── Step 2: Parse ────────────────────────────────
    console.print("[bold]② Parsing HTML with BeautifulSoup…[/bold]")
    soup = parse_html(html)

    text = extract_text(soup, tags)
    links = extract_links(soup, base_url=url)
    images = extract_images(soup, base_url=url)
    tables = extract_tables(soup)
    metadata = extract_metadata(soup)

    # Stats table
    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column(style="dim")
    stats.add_column(style="bold green")
    stats.add_row("Text length", f"{len(text):,} chars")
    stats.add_row("Links", str(len(links)))
    stats.add_row("Images", str(len(images)))
    stats.add_row("Tables", str(len(tables)))
    console.print(stats)
    console.print()

    # ── Step 3: LangChain pipeline ───────────────────
    scraped_data: dict = {
        "url": url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
        "text": text,
        "links": links,
        "images": images,
        "tables": tables,
    }

    # Create LangChain documents for LLM features
    docs = load_from_html(html, metadata={"source": url})
    chunks = split_documents(docs)
    console.print(f"[bold]③ LangChain pipeline:[/bold] {len(chunks)} document chunks")

    if args.summarize:
        console.print(f"  [dim]Running summarization via {args.provider}…[/dim]")
        summary = summarize_documents(chunks, provider=args.provider)
        scraped_data["summary"] = summary
        console.print(f"  [green]✓[/green] Summary generated ({len(summary)} chars)")

    if args.ask:
        console.print(f"  [dim]Answering question via {args.provider}…[/dim]")
        answer = qa_over_documents(chunks, args.ask, provider=args.provider)
        scraped_data["qa_question"] = args.ask
        scraped_data["qa_answer"] = answer
        console.print(f"  [green]✓[/green] Answer generated")

    console.print()

    # ── Step 4: Export ───────────────────────────────
    console.print("[bold]④ Exporting data…[/bold]")
    fmt = args.format

    # Build a unique filename from the page title + timestamp
    page_title = metadata.get("title", "scraped_page")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{_slugify(page_title)}_{timestamp}"
    console.print(f"  [dim]File base:[/dim] {base_name}")

    if fmt in ("json", "all"):
        p = export_json(scraped_data, output_dir / f"{base_name}.json")
        console.print(f"  [green]✓[/green] JSON  → {p}")

    if fmt in ("csv", "all"):
        p = export_csv(scraped_data, output_dir / f"{base_name}.csv")
        console.print(f"  [green]✓[/green] CSV   → {p.parent}")

    if fmt in ("md", "all"):
        p = export_markdown(scraped_data, output_dir / f"{base_name}.md")
        console.print(f"  [green]✓[/green] MD    → {p}")

    console.print()

    # ── Print summary / answer ───────────────────────
    if args.summarize and "summary" in scraped_data:
        console.print(Panel(
            scraped_data["summary"],
            title="[bold]AI Summary[/bold]",
            border_style="green",
            expand=False,
        ))
        console.print()

    if args.ask and "qa_answer" in scraped_data:
        console.print(Panel(
            f"[bold]Q:[/bold] {args.ask}\n\n"
            f"[bold]A:[/bold] {scraped_data['qa_answer']}",
            title="[bold]AI Q&A[/bold]",
            border_style="magenta",
            expand=False,
        ))
        console.print()

    console.print("[bold green]✓ Done![/bold green]\n")


# ─────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        run(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        sys.exit(130)
    except Exception as exc:
        console.print(f"\n[bold red]Error:[/bold red] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
