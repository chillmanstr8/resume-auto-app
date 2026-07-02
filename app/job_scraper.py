"""
job_scraper.py
Fetch and clean job descriptions from a URL.
"""

import re


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_job_description(url: str) -> str:
    """Scrape and return the job description text from *url*.

    Raises:
        RuntimeError: if the page cannot be fetched or parsed.
    """
    import requests
    from bs4 import BeautifulSoup

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Could not fetch job posting from {url!r}: {exc}") from exc

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "noscript", "iframe"]):
        tag.decompose()

    # Try common job-description container patterns (ordered by specificity)
    candidates = [
        soup.find(attrs={"id": re.compile(r"job[-_]?desc|jobDescription|posting", re.I)}),
        soup.find(attrs={"class": re.compile(r"job[-_]?desc|description|posting-detail|jobDetail", re.I)}),
        soup.find("article"),
        soup.find("main"),
        soup.find(attrs={"role": "main"}),
    ]

    for node in candidates:
        if node:
            text = node.get_text(separator="\n", strip=True)
            if len(text) >= 200:
                return _clean(text)

    # Fallback: full body
    body = soup.find("body") or soup
    return _clean(body.get_text(separator="\n", strip=True))


def clean_pasted_text(text: str) -> str:
    """Normalise user-pasted job-description text."""
    return _clean(text)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Remove excessive blank lines and deduplicate repeated lines."""
    lines = [ln.strip() for ln in text.splitlines()]

    # Keep unique, non-empty lines while preserving order
    seen: set[str] = set()
    cleaned: list[str] = []
    for line in lines:
        if not line:
            # Allow a single blank line as a separator, but collapse multiples
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        if line not in seen:
            seen.add(line)
            cleaned.append(line)

    # Strip leading/trailing blank lines
    while cleaned and cleaned[0] == "":
        cleaned.pop(0)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return "\n".join(cleaned)
