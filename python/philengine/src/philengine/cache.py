"""File-based embedding cache."""
from __future__ import annotations
import hashlib, os
from pathlib import Path
import numpy as np

class EmbeddingCache:
    def __init__(self, cache_dir: str | Path | None = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "phil" / "embeddings"
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _key(self, text: str, model: str) -> str:
        return hashlib.md5(f"{model}:{text}".encode()).hexdigest()

    def get(self, text: str, model: str) -> np.ndarray | None:
        path = self._dir / f"{self._key(text, model)}.npy"
        if path.exists():
            return np.load(path)
        return None

    def put(self, text: str, model: str, embedding: np.ndarray) -> None:
        path = self._dir / f"{self._key(text, model)}.npy"
        np.save(path, embedding)

    def clear(self) -> int:
        files = list(self._dir.glob("*.npy"))
        for f in files: f.unlink()
        return len(files)
