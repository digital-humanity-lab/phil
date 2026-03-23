"""J-STAGE data source for Japanese philosophy journals."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from philcorpus.sources.base import DataSource, RawDocument

logger = logging.getLogger(__name__)

JSTAGE_API = "https://api.jstage.jst.go.jp/searchapi/do"

# Target philosophy journals on J-STAGE
TARGET_JOURNALS: dict[str, dict[str, str]] = {
    "哲学研究": {
        "name_en": "Journal of Philosophical Studies",
        "affiliation": "Kyoto University",
    },
    "倫理学年報": {
        "name_en": "Annual Review of Ethics",
        "affiliation": "Japanese Society for Ethics",
    },
    "比較思想研究": {
        "name_en": "Studies in Comparative Philosophy",
        "affiliation": "Japanese Association for Comparative Philosophy",
    },
    "宗教研究": {
        "name_en": "Journal of Religious Studies",
        "affiliation": "Japanese Association for Religious Studies",
    },
    "科学哲学": {
        "name_en": "Philosophy of Science",
        "affiliation": "Philosophy of Science Society, Japan",
    },
}


def _parse_xml_response(xml_text: str) -> list[dict[str, Any]]:
    """Parse J-STAGE XML API response into a list of article dicts."""
    try:
        from lxml import etree
    except ImportError:
        logger.warning("lxml not installed; cannot parse J-STAGE XML response")
        return []

    articles: list[dict[str, Any]] = []
    try:
        root = etree.fromstring(xml_text.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        logger.warning("Failed to parse J-STAGE XML: %s", e)
        return []

    # J-STAGE returns entries in feed-like structure
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//entry", ns) or root.findall(".//entry"):
        article: dict[str, Any] = {}

        for tag, key in [
            ("article_title", "title"),
            ("author", "author"),
            ("pubyear", "year"),
            ("material_title", "journal"),
            ("doi", "doi"),
            ("cdjournal", "cdjournal"),
            ("link", "url"),
            ("pdf_url", "pdf_url"),
        ]:
            # Try with and without namespace
            elem = entry.find(tag)
            if elem is not None and elem.text:
                article[key] = elem.text.strip()

        # Also try namespaced elements
        for tag, key in [
            ("title", "title"),
            ("link", "url"),
        ]:
            if key not in article:
                elem = entry.find(f"atom:{tag}", ns)
                if elem is not None:
                    val = elem.text or elem.get("href", "")
                    if val:
                        article[key] = val.strip()

        if article.get("title"):
            articles.append(article)

    return articles


class JStageSource:
    """Fetch articles from J-STAGE Japanese philosophy journals.

    Parameters
    ----------
    journals : list[str] or None
        Journal names to search. Defaults to all target journals.
    """

    def __init__(self, journals: list[str] | None = None) -> None:
        self.journals = journals or list(TARGET_JOURNALS.keys())

    def fetch(
        self,
        query: str = "",
        limit: int = 100,
        pubyearfrom: int | None = None,
        pubyearto: int | None = None,
        lang: str | None = None,
    ) -> list[RawDocument]:
        """Fetch articles from J-STAGE.

        Parameters
        ----------
        query : str
            Search keyword.
        limit : int
            Maximum number of results per journal.
        pubyearfrom : int or None
            Start year filter.
        pubyearto : int or None
            End year filter.
        lang : str or None
            Language filter.

        Returns
        -------
        list[RawDocument]
            Fetched documents.
        """
        documents: list[RawDocument] = []

        for journal_name in self.journals:
            try:
                docs = self._fetch_journal(
                    journal_name,
                    query=query,
                    limit=limit,
                    pubyearfrom=pubyearfrom,
                    pubyearto=pubyearto,
                    lang=lang,
                )
                documents.extend(docs)
            except Exception as e:
                logger.warning(
                    "Failed to fetch from J-STAGE journal %s: %s",
                    journal_name,
                    e,
                )

        return documents

    def _fetch_journal(
        self,
        journal_name: str,
        query: str = "",
        limit: int = 100,
        pubyearfrom: int | None = None,
        pubyearto: int | None = None,
        lang: str | None = None,
    ) -> list[RawDocument]:
        """Fetch articles from a single J-STAGE journal."""
        params: dict[str, Any] = {
            "service": "3",
            "material": journal_name,
            "count": min(limit, 100),
            "start": 1,
        }
        if query:
            params["keyword"] = query
        if pubyearfrom:
            params["pubyearfrom"] = pubyearfrom
        if pubyearto:
            params["pubyearto"] = pubyearto
        if lang:
            params["lang"] = lang

        try:
            resp = httpx.get(JSTAGE_API, params=params, timeout=30.0)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("J-STAGE API error for %s: %s", journal_name, e)
            return []

        articles = _parse_xml_response(resp.text)
        documents: list[RawDocument] = []

        for article in articles[:limit]:
            year_str = article.get("year", "")
            try:
                year = int(year_str) if year_str else None
            except (ValueError, TypeError):
                year = None

            authors_raw = article.get("author", "")
            authors = (
                [a.strip() for a in authors_raw.split(";")]
                if authors_raw
                else []
            )

            doc = RawDocument(
                id=article.get("doi", article.get("url", "")),
                title=article.get("title", ""),
                authors=authors,
                year=year,
                language="ja",
                tradition="japanese",
                source="jstage",
                url=article.get("url", ""),
                fulltext_url=article.get("pdf_url"),
                metadata={
                    "journal": journal_name,
                    "journal_en": TARGET_JOURNALS.get(journal_name, {}).get(
                        "name_en", ""
                    ),
                },
            )
            documents.append(doc)

        return documents


def fetch_jstage(
    query: str = "",
    limit: int = 100,
    **kwargs: Any,
) -> list[RawDocument]:
    """Convenience function to fetch from J-STAGE philosophy journals.

    Parameters
    ----------
    query : str
        Search keyword.
    limit : int
        Maximum number of results per journal.
    **kwargs
        Additional arguments passed to JStageSource.fetch().

    Returns
    -------
    list[RawDocument]
        Fetched documents.
    """
    source = JStageSource()
    return source.fetch(query=query, limit=limit, **kwargs)
