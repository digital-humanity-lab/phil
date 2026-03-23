"""Base protocol and data models for corpus data sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class RawDocument:
    """A raw document fetched from a data source.

    Represents the minimum metadata needed to identify and retrieve a
    philosophical text from any source.
    """

    id: str
    title: str
    authors: list[str]
    year: int | None
    language: str
    tradition: str
    source: str
    url: str
    fulltext_url: str | None = None
    license: str | None = None
    abstract: str | None = None
    fulltext: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class DataSource(Protocol):
    """Protocol for data source connectors."""

    def fetch(self, query: str, limit: int = 100) -> list[RawDocument]:
        """Fetch documents matching the query.

        Parameters
        ----------
        query : str
            Search query string.
        limit : int
            Maximum number of documents to return.

        Returns
        -------
        list[RawDocument]
            List of raw documents matching the query.
        """
        ...
