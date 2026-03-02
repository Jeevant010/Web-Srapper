"""
HTTP fetcher with retries, custom headers, and error handling.
"""

import time
import requests
from rich.console import Console

from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, MAX_RETRIES

console = Console()


def fetch_page(url: str, headers: dict | None = None, timeout: int | None = None) -> requests.Response:
    """
    Fetch a web page with automatic retries and error handling.

    Args:
        url: The URL to fetch.
        headers: Optional custom headers (merged with defaults).
        timeout: Optional timeout override.

    Returns:
        requests.Response object.

    Raises:
        requests.HTTPError: If the request fails after all retries.
    """
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    _timeout = timeout or REQUEST_TIMEOUT

    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            console.print(f"  [dim]Attempt {attempt}/{MAX_RETRIES} — GET {url}[/dim]")
            response = requests.get(url, headers=merged_headers, timeout=_timeout)
            response.raise_for_status()

            # Detect encoding if not set
            if response.encoding is None or response.encoding == "ISO-8859-1":
                response.encoding = response.apparent_encoding

            console.print(f"  [green]✓[/green] {response.status_code} — {len(response.content)} bytes")
            return response

        except requests.RequestException as exc:
            last_exception = exc
            console.print(f"  [red]✗ Attempt {attempt} failed:[/red] {exc}")
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt
                console.print(f"  [dim]Retrying in {wait}s…[/dim]")
                time.sleep(wait)

    raise requests.HTTPError(
        f"Failed to fetch {url} after {MAX_RETRIES} attempts"
    ) from last_exception
