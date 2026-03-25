#!/usr/bin/env python3
"""Download and extract fulltext from OA philosophy papers that are NOT CC-BY/CC-BY-SA/public-domain.

Loads data/journal_fulltext/fulltext_urls.json, filters for non-CC-BY papers,
sorts by citation count, and processes the top 500.

For each paper:
1. Downloads PDF from pdf_url
2. Extracts text using PyMuPDF (fitz)
3. Saves to data/journal_fulltext/texts/{paper_id}.txt
"""

import json
import os
import sys
import time
import re
import logging
from pathlib import Path

# Try PyMuPDF first, fall back to pdfminer
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("WARNING: PyMuPDF not available. Install with: pip install PyMuPDF")

try:
    import requests
except ImportError:
    print("ERROR: requests not available. Install with: pip install requests")
    sys.exit(1)

# Setup
BASE_DIR = Path("/home/matsui/github/phil")
URLS_FILE = BASE_DIR / "data" / "journal_fulltext" / "fulltext_urls.json"
OUTPUT_DIR = BASE_DIR / "data" / "journal_fulltext" / "texts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDED_LICENSES = {"cc-by", "cc-by-sa", "public-domain"}
MAX_PAPERS = 500
RATE_LIMIT = 0.5  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds per request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def paper_id_to_filename(paper_id: str) -> str:
    """Convert OpenAlex ID to filename-safe string."""
    # e.g. "https://openalex.org/W1527720505" -> "W1527720505"
    return paper_id.split("/")[-1]


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    if not HAS_PYMUPDF:
        raise RuntimeError("PyMuPDF not installed")

    text_parts = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")

    return "\n".join(text_parts)


def extract_text_from_html(content: bytes) -> str:
    """Simple HTML text extraction fallback."""
    text = content.decode("utf-8", errors="replace")
    # Remove HTML tags
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def download_and_extract(pdf_url: str) -> str:
    """Download PDF and extract text."""
    headers = {
        "User-Agent": "PhilResearchBot/1.0 (academic research; mailto:matsui@example.com)",
        "Accept": "application/pdf,text/html,*/*",
    }

    resp = requests.get(pdf_url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "").lower()

    # Try PDF extraction first if content looks like PDF
    if content_type.startswith("application/pdf") or resp.content[:5] == b"%PDF-":
        return extract_text_from_pdf_bytes(resp.content)
    elif "html" in content_type:
        # HTML response - extract text from it
        return extract_text_from_html(resp.content)
    else:
        # Try as PDF anyway
        try:
            return extract_text_from_pdf_bytes(resp.content)
        except Exception:
            return extract_text_from_html(resp.content)


def main():
    if not HAS_PYMUPDF:
        log.error("PyMuPDF is required. Install with: pip install PyMuPDF")
        sys.exit(1)

    # Load data
    with open(URLS_FILE) as f:
        all_papers = json.load(f)
    log.info(f"Loaded {len(all_papers)} papers total")

    # Filter: exclude cc-by, cc-by-sa, public-domain; must have pdf_url
    target = [
        p for p in all_papers
        if p.get("license") not in EXCLUDED_LICENSES
        and p.get("pdf_url")
    ]
    log.info(f"Target papers (non CC-BY/CC-BY-SA/public-domain with pdf_url): {len(target)}")

    # Sort by citation count descending
    target.sort(key=lambda x: x.get("cited_by", 0), reverse=True)

    # Take top 500
    target = target[:MAX_PAPERS]
    log.info(f"Processing top {len(target)} by citation count")

    # Process
    downloaded = 0
    skipped = 0
    failed = 0

    for i, paper in enumerate(target):
        paper_id = paper_id_to_filename(paper["id"])
        output_path = OUTPUT_DIR / f"{paper_id}.txt"

        # Skip if already exists
        if output_path.exists() and output_path.stat().st_size > 0:
            skipped += 1
            continue

        title_short = paper.get("title", "")[:60]
        license_str = paper.get("license", "null")
        cited = paper.get("cited_by", 0)

        log.info(
            f"[{i+1}/{len(target)}] Downloading: {title_short}... "
            f"(cited={cited}, license={license_str})"
        )

        try:
            text = download_and_extract(paper["pdf_url"])

            if not text or len(text.strip()) < 100:
                log.warning(f"  -> Extracted text too short ({len(text.strip())} chars), skipping")
                failed += 1
                time.sleep(RATE_LIMIT)
                continue

            # Write metadata header + text
            with open(output_path, "w", encoding="utf-8") as out:
                out.write(f"# {paper.get('title', 'Unknown')}\n")
                out.write(f"# Authors: {', '.join(paper.get('authors', []))}\n")
                out.write(f"# Year: {paper.get('year', 'Unknown')}\n")
                out.write(f"# DOI: {paper.get('doi', 'Unknown')}\n")
                out.write(f"# License: {license_str}\n")
                out.write(f"# Citations: {cited}\n")
                out.write(f"# Source: {paper['pdf_url']}\n")
                out.write("\n")
                out.write(text)

            downloaded += 1
            log.info(f"  -> Saved {len(text)} chars to {paper_id}.txt")

        except requests.exceptions.Timeout:
            log.warning(f"  -> Timeout downloading {paper['pdf_url']}")
            failed += 1
        except requests.exceptions.HTTPError as e:
            log.warning(f"  -> HTTP error: {e}")
            failed += 1
        except Exception as e:
            log.warning(f"  -> Error: {e}")
            failed += 1

        # Rate limiting
        time.sleep(RATE_LIMIT)

    log.info(f"Done! Downloaded: {downloaded}, Skipped (existing): {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
