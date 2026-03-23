"""TEI XML text extraction (e.g., Perseus Digital Library format)."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

TEI_NS = "http://www.tei-c.org/ns/1.0"


def extract_text_from_tei(xml_content: str) -> str:
    """Extract text content from a TEI XML document.

    Handles the TEI format used by the Perseus Digital Library and
    similar scholarly text projects.

    Parameters
    ----------
    xml_content : str
        Raw TEI XML content.

    Returns
    -------
    str
        Extracted text content.
    """
    try:
        from lxml import etree

        return _extract_with_lxml(xml_content)
    except ImportError:
        logger.debug("lxml not available; using regex fallback for TEI")
        return _extract_with_regex(xml_content)


def _extract_with_lxml(xml_content: str) -> str:
    """Extract text from TEI using lxml."""
    from lxml import etree

    try:
        root = etree.fromstring(xml_content.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        logger.warning("Failed to parse TEI XML: %s", e)
        return _extract_with_regex(xml_content)

    ns = {"tei": TEI_NS}

    # Look for the body element
    body = root.find(".//tei:body", ns)
    if body is None:
        body = root.find(".//body")
    if body is None:
        body = root

    parts: list[str] = []

    # Extract text from div, p, l (line), and sp (speech) elements
    for elem in body.iter():
        tag = etree.QName(elem.tag).localname if isinstance(elem.tag, str) else ""
        if tag in ("p", "l", "sp", "head", "ab"):
            text = "".join(elem.itertext()).strip()
            if text:
                parts.append(text)

    if not parts:
        # Fallback: just get all text
        text = "".join(body.itertext()).strip()
        return text

    return "\n\n".join(parts)


def _extract_with_regex(xml_content: str) -> str:
    """Fallback regex-based TEI extraction."""
    # Remove XML declarations and processing instructions
    text = re.sub(r"<\?[^>]+\?>", "", xml_content)

    # Try to extract just the body
    body_match = re.search(
        r"<body[^>]*>(.*?)</body>", text, re.DOTALL | re.IGNORECASE
    )
    if body_match:
        text = body_match.group(1)

    # Remove XML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Clean whitespace
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
