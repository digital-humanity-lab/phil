"""CiNii Research data source for Japanese academic papers."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from philcorpus.sources.base import DataSource, RawDocument

logger = logging.getLogger(__name__)

CINII_API = "https://cir.nii.ac.jp/opensearch"


class CiNiiSource:
    """Fetch articles from CiNii Research (Japanese academic database).

    Uses the OpenSearch API to search for philosophy-related articles
    in Japanese academic journals.
    """

    def fetch(
        self,
        query: str = "哲学",
        limit: int = 100,
        lang: str = "ja",
    ) -> list[RawDocument]:
        """Fetch articles from CiNii Research.

        Parameters
        ----------
        query : str
            Search keyword (supports Japanese).
        limit : int
            Maximum number of results.
        lang : str
            Language preference.

        Returns
        -------
        list[RawDocument]
            Fetched documents.
        """
        documents: list[RawDocument] = []

        try:
            params: dict[str, Any] = {
                "q": query,
                "count": min(limit, 200),
                "lang": lang,
                "format": "atom",
            }
            resp = httpx.get(CINII_API, params=params, timeout=30.0)
            resp.raise_for_status()
            documents = self._parse_atom_response(resp.text, limit)

        except httpx.HTTPError as e:
            logger.warning("CiNii API error: %s", e)

        return documents[:limit]

    def _parse_atom_response(
        self, xml_text: str, limit: int
    ) -> list[RawDocument]:
        """Parse CiNii Atom/XML response."""
        try:
            from lxml import etree
        except ImportError:
            logger.warning("lxml not installed; cannot parse CiNii XML")
            return []

        documents: list[RawDocument] = []

        try:
            root = etree.fromstring(xml_text.encode("utf-8"))
        except etree.XMLSyntaxError as e:
            logger.warning("Failed to parse CiNii XML: %s", e)
            return []

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "prism": "http://prismstandard.org/namespaces/basic/2.0/",
        }

        for entry in root.findall("atom:entry", ns)[:limit]:
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

            link_elem = entry.find('atom:link[@rel="alternate"]', ns)
            if link_elem is None:
                link_elem = entry.find("atom:link", ns)
            url = link_elem.get("href", "") if link_elem is not None else ""

            id_elem = entry.find("atom:id", ns)
            doc_id = id_elem.text.strip() if id_elem is not None and id_elem.text else url

            authors: list[str] = []
            for author_elem in entry.findall("atom:author/atom:name", ns):
                if author_elem.text:
                    authors.append(author_elem.text.strip())
            # Also check dc:creator
            for creator_elem in entry.findall("dc:creator", ns):
                if creator_elem.text and creator_elem.text.strip() not in authors:
                    authors.append(creator_elem.text.strip())

            year = None
            date_elem = entry.find("prism:publicationDate", ns)
            if date_elem is not None and date_elem.text:
                try:
                    year = int(date_elem.text[:4])
                except (ValueError, IndexError):
                    pass
            if year is None:
                published_elem = entry.find("atom:published", ns)
                if published_elem is not None and published_elem.text:
                    try:
                        year = int(published_elem.text[:4])
                    except (ValueError, IndexError):
                        pass

            doc = RawDocument(
                id=doc_id,
                title=title,
                authors=authors,
                year=year,
                language="ja",
                tradition="japanese",
                source="cinii",
                url=url,
            )
            documents.append(doc)

        return documents
