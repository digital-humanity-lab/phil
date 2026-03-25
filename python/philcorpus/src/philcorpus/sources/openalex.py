"""OpenAlex data source for open-access philosophy papers."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from philcorpus.sources.base import DataSource, RawDocument

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org"
PHILOSOPHY_CONCEPT_ID = "C138885662"


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Reconstruct abstract text from OpenAlex inverted index format."""
    if not inverted_index:
        return None
    word_positions: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in word_positions)


class OpenAlexSource:
    """Fetch open-access philosophy papers from OpenAlex.

    Parameters
    ----------
    email : str
        Contact email for polite pool (higher rate limits).
    """

    def __init__(self, email: str = "digital-philosophy@example.com") -> None:
        self.email = email
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Enforce rate limiting (max 10 requests/second)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)
        self._last_request_time = time.time()

    def fetch(
        self,
        query: str = "philosophy",
        tradition: str | None = None,
        language: str | None = None,
        is_oa: bool = True,
        has_fulltext: bool = True,
        limit: int = 100,
    ) -> list[RawDocument]:
        """Fetch philosophy papers from OpenAlex.

        Parameters
        ----------
        query : str
            Search query or topic.
        tradition : str or None
            Philosophical tradition to filter by (used in metadata).
        language : str or None
            Language filter (ISO 639-1 code).
        is_oa : bool
            Only return open-access works.
        has_fulltext : bool
            Only return works with fulltext available.
        limit : int
            Maximum number of results.

        Returns
        -------
        list[RawDocument]
            Fetched documents.
        """
        filters = [f"concepts.id:{PHILOSOPHY_CONCEPT_ID}"]
        if is_oa:
            filters.append("is_oa:true")
        if has_fulltext:
            filters.append("has_fulltext:true")
        if language:
            filters.append(f"language:{language}")

        filter_str = ",".join(filters)
        documents: list[RawDocument] = []
        cursor = "*"

        try:
            while len(documents) < limit:
                self._rate_limit()
                params: dict[str, Any] = {
                    "mailto": self.email,
                    "filter": filter_str,
                    "search": query,
                    "per_page": min(200, limit - len(documents)),
                    "cursor": cursor,
                }
                resp = httpx.get(
                    f"{BASE_URL}/works",
                    params=params,
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    break

                for work in results:
                    doc = self._parse_work(work, tradition or "western")
                    documents.append(doc)

                cursor = data.get("meta", {}).get("next_cursor")
                if not cursor:
                    break

        except httpx.HTTPError as e:
            logger.warning("OpenAlex API error: %s", e)

        return documents[:limit]

    def _parse_work(self, work: dict[str, Any], tradition: str) -> RawDocument:
        """Parse an OpenAlex work record into a RawDocument."""
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in work.get("authorships", [])
        ]
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

        # Find best OA location for fulltext
        best_oa = work.get("best_oa_location") or {}
        fulltext_url = best_oa.get("pdf_url") or best_oa.get("landing_page_url")
        license_str = best_oa.get("license")

        return RawDocument(
            id=work.get("id", ""),
            title=work.get("title", ""),
            authors=[a for a in authors if a],
            year=work.get("publication_year"),
            language=work.get("language", "en"),
            tradition=tradition,
            source="openalex",
            url=work.get("doi") or work.get("id", ""),
            fulltext_url=fulltext_url,
            license=license_str,
            abstract=abstract,
            metadata={
                "cited_by_count": work.get("cited_by_count", 0),
                "concepts": [
                    c.get("display_name", "")
                    for c in work.get("concepts", [])[:5]
                ],
                "type": work.get("type", ""),
            },
        )

    def fetch_fulltext(self, doc: RawDocument) -> str | None:
        """Download fulltext for a document.

        Attempts to download the PDF and extract text, or falls back to
        the landing page.

        Parameters
        ----------
        doc : RawDocument
            Document with fulltext_url set.

        Returns
        -------
        str or None
            Extracted text content, or None if unavailable.
        """
        if not doc.fulltext_url:
            return None

        try:
            self._rate_limit()
            resp = httpx.get(
                doc.fulltext_url,
                timeout=60.0,
                follow_redirects=True,
            )
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "pdf" in content_type:
                try:
                    from philcorpus.extract.pdf import extract_text_from_pdf

                    return extract_text_from_pdf(resp.content)
                except ImportError:
                    logger.warning(
                        "pymupdf not installed; cannot extract PDF text"
                    )
                    return None
            elif "html" in content_type:
                from philcorpus.extract.html import extract_text_from_html

                return extract_text_from_html(resp.text)
            else:
                return resp.text

        except httpx.HTTPError as e:
            logger.warning("Failed to fetch fulltext for %s: %s", doc.id, e)
            return None


def fetch_oa_papers(
    query: str = "philosophy",
    limit: int = 100,
    **kwargs: Any,
) -> list[RawDocument]:
    """Convenience function to fetch open-access philosophy papers.

    Parameters
    ----------
    query : str
        Search query.
    limit : int
        Maximum number of results.
    **kwargs
        Additional arguments passed to OpenAlexSource.fetch().

    Returns
    -------
    list[RawDocument]
        Fetched documents.
    """
    source = OpenAlexSource()
    return source.fetch(query=query, limit=limit, **kwargs)
