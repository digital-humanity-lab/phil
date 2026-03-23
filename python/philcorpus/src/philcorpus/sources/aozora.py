"""Aozora Bunko data source for Japanese public domain philosophy texts."""

from __future__ import annotations

import csv
import io
import logging
import time
from typing import Any

import httpx

from philcorpus.sources.base import DataSource, RawDocument

logger = logging.getLogger(__name__)

CSV_INDEX_URL = "https://www.aozora.gr.jp/index_pages/person_all_extended.csv"
GITHUB_MIRROR = "https://github.com/aozorabunko/aozorabunko"
GITHUB_RAW = "https://raw.githubusercontent.com/aozorabunko/aozorabunko/master"

# Target Japanese philosophers
TARGET_AUTHORS: dict[str, str] = {
    "西田幾多郎": "Kitaro Nishida",
    "和辻哲郎": "Tetsuro Watsuji",
    "九鬼周造": "Shuzo Kuki",
    "三木清": "Kiyoshi Miki",
    "田辺元": "Hajime Tanabe",
}


class AozoraSource:
    """Fetch Japanese philosophy texts from Aozora Bunko.

    Aozora Bunko is a digital library of Japanese public domain works,
    including texts by major Japanese philosophers.

    Parameters
    ----------
    authors : dict[str, str] or None
        Mapping of Japanese author names to romanized names.
        Defaults to the built-in TARGET_AUTHORS.
    """

    def __init__(
        self, authors: dict[str, str] | None = None
    ) -> None:
        self.authors = authors or TARGET_AUTHORS
        self._index: list[dict[str, str]] | None = None

    def _load_index(self) -> list[dict[str, str]]:
        """Download and parse the Aozora Bunko CSV index."""
        if self._index is not None:
            return self._index

        try:
            resp = httpx.get(
                CSV_INDEX_URL,
                timeout=60.0,
                follow_redirects=True,
            )
            resp.raise_for_status()

            # Aozora CSV uses Shift_JIS encoding
            text = resp.content.decode("shift_jis", errors="replace")
            reader = csv.DictReader(io.StringIO(text))
            self._index = list(reader)
            return self._index

        except httpx.HTTPError as e:
            logger.warning("Failed to download Aozora index: %s", e)
            self._index = []
            return self._index
        except Exception as e:
            logger.warning("Failed to parse Aozora index: %s", e)
            self._index = []
            return self._index

    def fetch(
        self,
        query: str = "",
        limit: int = 100,
        download_fulltext: bool = False,
    ) -> list[RawDocument]:
        """Fetch works by target Japanese philosophers from Aozora Bunko.

        Parameters
        ----------
        query : str
            Filter by title (substring match, supports Japanese).
        limit : int
            Maximum number of results.
        download_fulltext : bool
            If True, download full text of each work.

        Returns
        -------
        list[RawDocument]
            Fetched documents.
        """
        index = self._load_index()
        if not index:
            return []

        documents: list[RawDocument] = []

        for entry in index:
            author_name = entry.get("姓") or ""
            first_name = entry.get("名") or ""
            full_name = f"{author_name}{first_name}"

            if full_name not in self.authors:
                continue

            title = entry.get("作品名", "")
            if query and query not in title:
                continue

            text_url = entry.get("テキストファイルURL", "")
            html_url = entry.get("XHTML/HTMLファイルURL", "")

            fulltext = None
            if download_fulltext and text_url:
                fulltext = self._download_text(text_url)
                time.sleep(0.5)

            person_id = entry.get("人物ID", "")
            work_id = entry.get("作品ID", "")
            doc_id = f"aozora:{person_id}:{work_id}" if person_id and work_id else f"aozora:{title}"

            doc = RawDocument(
                id=doc_id,
                title=title,
                authors=[full_name],
                year=None,
                language="ja",
                tradition="japanese",
                source="aozora",
                url=html_url or text_url or f"https://www.aozora.gr.jp/",
                fulltext_url=text_url or html_url,
                license="public_domain",
                fulltext=fulltext,
                metadata={
                    "author_ja": full_name,
                    "author_en": self.authors.get(full_name, ""),
                    "person_id": person_id,
                    "work_id": work_id,
                },
            )
            documents.append(doc)

            if len(documents) >= limit:
                break

        return documents

    def _download_text(self, url: str) -> str | None:
        """Download text content from Aozora Bunko."""
        try:
            resp = httpx.get(
                url,
                timeout=30.0,
                follow_redirects=True,
            )
            resp.raise_for_status()
            # Aozora texts are typically Shift_JIS encoded
            try:
                return resp.content.decode("shift_jis")
            except UnicodeDecodeError:
                return resp.text
        except httpx.HTTPError as e:
            logger.warning("Failed to download Aozora text: %s", e)
            return None


def fetch_aozora(
    query: str = "",
    limit: int = 100,
    **kwargs: Any,
) -> list[RawDocument]:
    """Convenience function to fetch Aozora Bunko philosophy texts.

    Parameters
    ----------
    query : str
        Filter by title.
    limit : int
        Maximum number of results.
    **kwargs
        Additional arguments passed to AozoraSource.fetch().

    Returns
    -------
    list[RawDocument]
        Fetched documents.
    """
    source = AozoraSource()
    return source.fetch(query=query, limit=limit, **kwargs)
