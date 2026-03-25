"""Download registry to track fetched documents and avoid re-downloading."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_PATH = Path.home() / ".cache" / "philcorpus" / "registry.json"


class FetchRegistry:
    """Track which documents have already been fetched.

    Uses a simple JSON file to persist the registry between sessions.

    Parameters
    ----------
    path : Path or str or None
        Path to the registry JSON file. Defaults to
        ``~/.cache/philcorpus/registry.json``.
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_REGISTRY_PATH
        self._entries: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load the registry from disk."""
        if self.path.exists():
            try:
                with open(self.path) as f:
                    self._entries = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load registry: %s", e)
                self._entries = {}

    def _save(self) -> None:
        """Persist the registry to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.path, "w") as f:
                json.dump(self._entries, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning("Failed to save registry: %s", e)

    def is_fetched(self, doc_id: str) -> bool:
        """Check whether a document has already been fetched.

        Parameters
        ----------
        doc_id : str
            Unique document identifier.

        Returns
        -------
        bool
            True if the document is in the registry.
        """
        return doc_id in self._entries

    def mark_fetched(
        self,
        doc_id: str,
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record that a document has been fetched.

        Parameters
        ----------
        doc_id : str
            Unique document identifier.
        source : str
            Source name (e.g., "openalex", "gutenberg").
        metadata : dict or None
            Optional metadata about the fetch.
        """
        self._entries[doc_id] = {
            "source": source,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }
        self._save()

    def list_fetched(self) -> list[str]:
        """Return all fetched document IDs.

        Returns
        -------
        list[str]
            List of document IDs in the registry.
        """
        return list(self._entries.keys())

    def clear(self) -> None:
        """Clear the entire registry."""
        self._entries = {}
        self._save()

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, doc_id: str) -> bool:
        return self.is_fetched(doc_id)
