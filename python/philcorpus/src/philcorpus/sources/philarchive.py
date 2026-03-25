"""PhilArchive data source for open philosophy papers."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from philcorpus.sources.base import DataSource, RawDocument

logger = logging.getLogger(__name__)

PHILARCHIVE_BASE = "https://philarchive.org"


class PhilArchiveSource:
    """Fetch philosophy papers from PhilArchive via HTTP scraping.

    PhilArchive hosts open-access philosophy papers organized by
    category and searchable by keyword.
    """

    def fetch(
        self,
        query: str = "philosophy",
        category: str | None = None,
        limit: int = 100,
    ) -> list[RawDocument]:
        """Fetch papers from PhilArchive.

        Parameters
        ----------
        query : str
            Search keyword.
        category : str or None
            PhilArchive category to browse.
        limit : int
            Maximum number of results.

        Returns
        -------
        list[RawDocument]
            Fetched documents.
        """
        documents: list[RawDocument] = []

        try:
            if category:
                url = f"{PHILARCHIVE_BASE}/browse/{category}"
            else:
                url = f"{PHILARCHIVE_BASE}/search"

            params: dict[str, Any] = {"q": query, "limit": min(limit, 100)}
            resp = httpx.get(
                url,
                params=params,
                timeout=30.0,
                follow_redirects=True,
            )
            resp.raise_for_status()

            documents = self._parse_search_results(resp.text, limit)

        except httpx.HTTPError as e:
            logger.warning("PhilArchive request error: %s", e)
        except Exception as e:
            logger.warning("PhilArchive parsing error: %s", e)

        return documents[:limit]

    def _parse_search_results(
        self, html: str, limit: int
    ) -> list[RawDocument]:
        """Parse PhilArchive search results HTML."""
        documents: list[RawDocument] = []

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
        except ImportError:
            # Fallback to basic regex parsing
            return self._parse_with_regex(html, limit)

        for item in soup.select(".entryList .entry, .searchResult")[:limit]:
            title_elem = item.select_one("a.entryTitle, .title a, h3 a")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            href = title_elem.get("href", "")
            url = href if href.startswith("http") else f"{PHILARCHIVE_BASE}{href}"

            authors_elem = item.select_one(".authors, .entryAuthors")
            authors_text = (
                authors_elem.get_text(strip=True) if authors_elem else ""
            )
            authors = [
                a.strip() for a in re.split(r"[,;&]", authors_text) if a.strip()
            ]

            year_elem = item.select_one(".year, .entryDate")
            year_text = year_elem.get_text(strip=True) if year_elem else ""
            year_match = re.search(r"\b(19|20)\d{2}\b", year_text)
            year = int(year_match.group()) if year_match else None

            pdf_link = item.select_one("a[href$='.pdf']")
            pdf_url = None
            if pdf_link:
                href = pdf_link.get("href", "")
                pdf_url = (
                    href
                    if href.startswith("http")
                    else f"{PHILARCHIVE_BASE}{href}"
                )

            doc = RawDocument(
                id=url,
                title=title,
                authors=authors,
                year=year,
                language="en",
                tradition="western",
                source="philarchive",
                url=url,
                fulltext_url=pdf_url,
            )
            documents.append(doc)

        return documents

    def _parse_with_regex(self, html: str, limit: int) -> list[RawDocument]:
        """Fallback regex-based parsing when BeautifulSoup is unavailable."""
        documents: list[RawDocument] = []

        # Simple pattern to find linked titles
        pattern = r'<a[^>]*href="(/rec/[^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html)

        for href, title in matches[:limit]:
            url = f"{PHILARCHIVE_BASE}{href}"
            doc = RawDocument(
                id=url,
                title=title.strip(),
                authors=[],
                year=None,
                language="en",
                tradition="western",
                source="philarchive",
                url=url,
            )
            documents.append(doc)

        return documents
