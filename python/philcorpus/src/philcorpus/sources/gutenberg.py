"""Project Gutenberg data source for classical philosophy texts."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from philcorpus.sources.base import DataSource, RawDocument

logger = logging.getLogger(__name__)

# Classical philosophy texts available on Project Gutenberg
PHILOSOPHY_WORKS: list[dict[str, Any]] = [
    {"id": 1497, "title": "Republic", "author": "Plato", "tradition": "greek"},
    {"id": 1656, "title": "Apology", "author": "Plato", "tradition": "greek"},
    {"id": 1636, "title": "Symposium", "author": "Plato", "tradition": "greek"},
    {"id": 1658, "title": "Phaedo", "author": "Plato", "tradition": "greek"},
    {"id": 5827, "title": "Critique of Pure Reason", "author": "Immanuel Kant", "tradition": "german"},
    {"id": 4280, "title": "Critique of Practical Reason", "author": "Immanuel Kant", "tradition": "german"},
    {"id": 5740, "title": "Meditations", "author": "Marcus Aurelius", "tradition": "roman"},
    {"id": 3600, "title": "An Essay Concerning Human Understanding", "author": "John Locke", "tradition": "british"},
    {"id": 4705, "title": "A Treatise of Human Nature", "author": "David Hume", "tradition": "british"},
    {"id": 10615, "title": "Meditations on First Philosophy", "author": "Rene Descartes", "tradition": "continental"},
    {"id": 1232, "title": "The Prince", "author": "Niccolo Machiavelli", "tradition": "italian"},
    {"id": 7370, "title": "Beyond Good and Evil", "author": "Friedrich Nietzsche", "tradition": "german"},
    {"id": 38427, "title": "Thus Spake Zarathustra", "author": "Friedrich Nietzsche", "tradition": "german"},
    {"id": 30821, "title": "On Liberty", "author": "John Stuart Mill", "tradition": "british"},
    {"id": 11224, "title": "Leviathan", "author": "Thomas Hobbes", "tradition": "british"},
    {"id": 9662, "title": "The Nicomachean Ethics", "author": "Aristotle", "tradition": "greek"},
    {"id": 8438, "title": "Politics", "author": "Aristotle", "tradition": "greek"},
]


def _fetch_text(gutenberg_id: int) -> str | None:
    """Download plain text from Gutenberg mirrors."""
    urls = [
        f"https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.txt",
        f"https://www.gutenberg.org/files/{gutenberg_id}/{gutenberg_id}-0.txt",
    ]
    for url in urls:
        try:
            resp = httpx.get(url, timeout=30.0, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
        except httpx.HTTPError:
            continue
    return None


class GutenbergSource:
    """Fetch classical philosophy texts from Project Gutenberg.

    Provides access to public domain philosophical works through
    the Project Gutenberg plain text mirrors.
    """

    def __init__(
        self, works: list[dict[str, Any]] | None = None
    ) -> None:
        self.works = works or PHILOSOPHY_WORKS

    def fetch(
        self,
        query: str = "",
        limit: int = 100,
        download_fulltext: bool = False,
    ) -> list[RawDocument]:
        """Fetch Gutenberg philosophy texts.

        Parameters
        ----------
        query : str
            Filter by title or author (case-insensitive substring match).
        limit : int
            Maximum number of results.
        download_fulltext : bool
            If True, download the full text of each work.

        Returns
        -------
        list[RawDocument]
            Fetched documents.
        """
        query_lower = query.lower()
        filtered = [
            w
            for w in self.works
            if not query
            or query_lower in w["title"].lower()
            or query_lower in w["author"].lower()
        ][:limit]

        documents: list[RawDocument] = []
        for work in filtered:
            gid = work["id"]
            fulltext_url = (
                f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
            )

            fulltext = None
            if download_fulltext:
                logger.info(
                    "Downloading: %s - %s", work["author"], work["title"]
                )
                fulltext = _fetch_text(gid)
                time.sleep(1.0)  # Be polite to Gutenberg

            doc = RawDocument(
                id=f"gutenberg:{gid}",
                title=work["title"],
                authors=[work["author"]],
                year=None,  # Historical texts, publication year varies
                language="en",
                tradition=work.get("tradition", "western"),
                source="gutenberg",
                url=f"https://www.gutenberg.org/ebooks/{gid}",
                fulltext_url=fulltext_url,
                license="public_domain",
                fulltext=fulltext,
            )
            documents.append(doc)

        return documents


def fetch_gutenberg(
    query: str = "",
    limit: int = 100,
    **kwargs: Any,
) -> list[RawDocument]:
    """Convenience function to fetch Gutenberg philosophy texts.

    Parameters
    ----------
    query : str
        Filter by title or author.
    limit : int
        Maximum number of results.
    **kwargs
        Additional arguments passed to GutenbergSource.fetch().

    Returns
    -------
    list[RawDocument]
        Fetched documents.
    """
    source = GutenbergSource()
    return source.fetch(query=query, limit=limit, **kwargs)
