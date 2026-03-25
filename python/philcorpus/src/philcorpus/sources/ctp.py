"""Chinese Text Project data source for classical Chinese philosophy."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from philcorpus.sources.base import DataSource, RawDocument

logger = logging.getLogger(__name__)

BASE_URL = "https://api.ctext.org"

# Core philosophical texts organized by tradition
TEXTS: dict[str, list[dict[str, str]]] = {
    "confucianism": [
        {"urn": "ctp:analects", "title": "論語", "title_en": "Analerta"},
        {"urn": "ctp:mengzi", "title": "孟子", "title_en": "Mengzi"},
        {"urn": "ctp:daxue", "title": "大学", "title_en": "Great Learning"},
        {"urn": "ctp:zhongyong", "title": "中庸", "title_en": "Doctrine of the Mean"},
        {"urn": "ctp:xunzi", "title": "荀子", "title_en": "Xunzi"},
    ],
    "daoism": [
        {"urn": "ctp:dao-de-jing", "title": "道徳経", "title_en": "Dao De Jing"},
        {"urn": "ctp:zhuangzi", "title": "荘子", "title_en": "Zhuangzi"},
    ],
    "legalism": [
        {"urn": "ctp:han-feizi", "title": "韓非子", "title_en": "Han Feizi"},
    ],
    "mohism": [
        {"urn": "ctp:mozi", "title": "墨子", "title_en": "Mozi"},
    ],
    "buddhism": [
        {"urn": "ctp:heart-sutra", "title": "般若心経", "title_en": "Heart Sutra"},
    ],
}


def _get_text_info(urn: str) -> dict[str, Any] | None:
    """Get metadata about a text from CTP API."""
    try:
        resp = httpx.get(
            f"{BASE_URL}/gettextinfo",
            params={"urn": urn},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Error fetching CTP info for %s: %s", urn, e)
        return None


def _get_text_content(urn: str) -> dict[str, Any] | None:
    """Get text content for a chapter/section from CTP API."""
    try:
        resp = httpx.get(
            f"{BASE_URL}/gettext",
            params={"urn": urn},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Error fetching CTP text %s: %s", urn, e)
        return None


class CTPSource:
    """Fetch classical Chinese philosophical texts from the Chinese Text Project.

    Provides access to Confucian, Daoist, Buddhist, Legalist, and Mohist
    classical texts through the CTP API.
    """

    def __init__(
        self, traditions: list[str] | None = None
    ) -> None:
        self.traditions = traditions or list(TEXTS.keys())

    def fetch(
        self,
        query: str = "",
        limit: int = 100,
        download_fulltext: bool = False,
        max_chapters: int = 5,
    ) -> list[RawDocument]:
        """Fetch Chinese classical philosophy texts.

        Parameters
        ----------
        query : str
            Filter by title (substring match).
        limit : int
            Maximum number of results.
        download_fulltext : bool
            If True, fetch chapter content for each text.
        max_chapters : int
            Maximum number of chapters to fetch per text.

        Returns
        -------
        list[RawDocument]
            Fetched documents.
        """
        documents: list[RawDocument] = []
        query_lower = query.lower()

        for tradition in self.traditions:
            if tradition not in TEXTS:
                continue

            for text_info in TEXTS[tradition]:
                if query and query_lower not in text_info["title_en"].lower():
                    if query_lower not in text_info["title"]:
                        continue

                fulltext = None
                if download_fulltext:
                    fulltext = self._fetch_chapters(
                        text_info["urn"], max_chapters
                    )

                doc = RawDocument(
                    id=text_info["urn"],
                    title=f"{text_info['title']} ({text_info['title_en']})",
                    authors=[],
                    year=None,
                    language="zh",
                    tradition=tradition,
                    source="ctp",
                    url=f"https://ctext.org/{text_info['urn'].replace('ctp:', '')}",
                    fulltext=fulltext,
                    metadata={
                        "urn": text_info["urn"],
                        "title_zh": text_info["title"],
                        "title_en": text_info["title_en"],
                    },
                )
                documents.append(doc)

                if len(documents) >= limit:
                    return documents

        return documents

    def _fetch_chapters(self, urn: str, max_chapters: int) -> str | None:
        """Fetch and concatenate chapter content for a text."""
        info = _get_text_info(urn)
        if not info:
            return None

        subsections = info.get("subsections", [])
        if not subsections:
            content = _get_text_content(urn)
            if content:
                return str(content)
            return None

        parts: list[str] = []
        for sub in subsections[:max_chapters]:
            sub_urn = sub if isinstance(sub, str) else sub.get("urn", "")
            if not sub_urn:
                continue
            time.sleep(0.5)
            content = _get_text_content(sub_urn)
            if content:
                parts.append(str(content))

        return "\n\n".join(parts) if parts else None


def fetch_ctp(
    query: str = "",
    limit: int = 100,
    **kwargs: Any,
) -> list[RawDocument]:
    """Convenience function to fetch Chinese classical philosophy texts.

    Parameters
    ----------
    query : str
        Filter by title.
    limit : int
        Maximum number of results.
    **kwargs
        Additional arguments passed to CTPSource.fetch().

    Returns
    -------
    list[RawDocument]
        Fetched documents.
    """
    source = CTPSource()
    return source.fetch(query=query, limit=limit, **kwargs)
