"""HTML text extraction."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Tags whose content should be stripped entirely
_STRIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "noscript"}


def extract_text_from_html(html_content: str) -> str:
    """Extract main text content from an HTML page.

    Uses BeautifulSoup if available, otherwise falls back to regex-based
    extraction.

    Parameters
    ----------
    html_content : str
        Raw HTML content.

    Returns
    -------
    str
        Extracted text content.
    """
    try:
        from bs4 import BeautifulSoup

        return _extract_with_bs4(html_content)
    except ImportError:
        logger.debug("beautifulsoup4 not available; using regex fallback")
        return _extract_with_regex(html_content)


def _extract_with_bs4(html_content: str) -> str:
    """Extract text using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unwanted elements
    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    # Try to find main content area
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", class_=re.compile(r"content|article|body", re.I))
        or soup.find("body")
        or soup
    )

    text = main.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def _extract_with_regex(html_content: str) -> str:
    """Fallback regex-based HTML text extraction."""
    text = html_content

    # Remove script and style blocks
    text = re.sub(
        r"<(script|style|nav|header|footer)[^>]*>.*?</\1>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode common HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")

    # Clean up whitespace
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
