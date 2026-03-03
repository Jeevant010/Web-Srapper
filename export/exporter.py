"""
Export scraped data to JSON, CSV, and Markdown formats.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime, timezone


def export_json(data: dict, path: Path) -> Path:
    """
    Export the full scraped data dict as formatted JSON.

    Args:
        data: The scraped data dictionary.
        path: Output file path.

    Returns:
        The path the file was written to.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    return path


def export_csv(data: dict, path: Path) -> Path:
    """
    Export links, images, and tables as CSV.
    Creates separate CSV files for each data type.

    Args:
        data: The scraped data dictionary.
        path: Base output file path (will be suffixed).

    Returns:
        The base path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    base = path.stem
    directory = path.parent

    # ── Links CSV ─────────────────────────────────────
    links = data.get("links", [])
    if links:
        links_path = directory / f"{base}_links.csv"
        with open(links_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["text", "href", "title"])
            writer.writeheader()
            writer.writerows(links)

    # ── Images CSV ────────────────────────────────────
    images = data.get("images", [])
    if images:
        images_path = directory / f"{base}_images.csv"
        with open(images_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["src", "alt", "width", "height"])
            writer.writeheader()
            writer.writerows(images)

    # ── Tables CSV ────────────────────────────────────
    tables = data.get("tables", [])
    for i, table in enumerate(tables):
        table_path = directory / f"{base}_table_{i + 1}.csv"
        with open(table_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(table)

    return path


def export_markdown(data: dict, path: Path) -> Path:
    """
    Export a human-readable Markdown report.

    Args:
        data: The scraped data dictionary.
        path: Output file path.

    Returns:
        The path the file was written to.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = data.get("metadata", {})
    lines: list[str] = []

    # Header
    title = meta.get("title", "Untitled Page")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"> Scraped at: {data.get('scraped_at', 'N/A')}")
    lines.append(f"> URL: {data.get('url', 'N/A')}")
    lines.append("")

    # Metadata
    if meta:
        lines.append("## Page Metadata")
        lines.append("")
        if meta.get("description"):
            lines.append(f"**Description:** {meta['description']}")
        if meta.get("canonical_url"):
            lines.append(f"**Canonical URL:** {meta['canonical_url']}")
        if meta.get("language"):
            lines.append(f"**Language:** {meta['language']}")
        og = meta.get("og", {})
        if og:
            lines.append("")
            lines.append("### Open Graph Tags")
            for key, val in og.items():
                lines.append(f"- `{key}`: {val}")
        lines.append("")

    # Text Content
    text = data.get("text", "")
    if text:
        lines.append("## Extracted Text")
        lines.append("")
        lines.append(text)
        lines.append("")

    # Links
    links = data.get("links", [])
    if links:
        lines.append(f"## Links ({len(links)} found)")
        lines.append("")
        for link in links:
            text_label = link.get("text", "[no text]")
            href = link.get("href", "")
            lines.append(f"- [{text_label}]({href})")
        lines.append("")

    # Images
    images = data.get("images", [])
    if images:
        lines.append(f"## Images ({len(images)} found)")
        lines.append("")
        for img in images:
            alt = img.get("alt", "no alt")
            src = img.get("src", "")
            lines.append(f"- `{alt}` → {src}")
        lines.append("")

    # Tables
    tables = data.get("tables", [])
    if tables:
        lines.append(f"## Tables ({len(tables)} found)")
        lines.append("")
        for i, table in enumerate(tables):
            lines.append(f"### Table {i + 1}")
            lines.append("")
            if table:
                # Use first row as header
                header = table[0]
                lines.append("| " + " | ".join(header) + " |")
                lines.append("| " + " | ".join(["---"] * len(header)) + " |")
                for row in table[1:]:
                    # Pad row to match header length
                    padded = row + [""] * (len(header) - len(row))
                    lines.append("| " + " | ".join(padded[:len(header)]) + " |")
            lines.append("")

    # Summary (if available)
    summary = data.get("summary", "")
    if summary:
        lines.append("## AI Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # Q&A (if available)
    qa = data.get("qa_answer", "")
    if qa:
        lines.append("## AI Q&A")
        lines.append("")
        lines.append(f"**Question:** {data.get('qa_question', '')}")
        lines.append("")
        lines.append(f"**Answer:** {qa}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
