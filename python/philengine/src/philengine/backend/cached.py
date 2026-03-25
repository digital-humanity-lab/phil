"""Caching wrapper for any embedding backend."""
from __future__ import annotations
import hashlib
import numpy as np
from .base import BackendMetadata

class CachedBackend:
    def __init__(self, backend, max_cache_size: int = 10000):
        self._backend = backend
        self._cache: dict[str, np.ndarray] = {}
        self._max_cache_size = max_cache_size

    def _cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        results = []
        uncached_texts = []
        uncached_indices = []
        for i, text in enumerate(texts):
            key = self._cache_key(text)
            if key in self._cache:
                results.append((i, self._cache[key]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        if uncached_texts:
            new_embeddings = self._backend.encode(uncached_texts, **kwargs)
            for j, idx in enumerate(uncached_indices):
                key = self._cache_key(texts[idx])
                if len(self._cache) < self._max_cache_size:
                    self._cache[key] = new_embeddings[j]
                results.append((idx, new_embeddings[j]))

        results.sort(key=lambda x: x[0])
        return np.stack([r[1] for r in results])

    def dim(self) -> int: return self._backend.dim()
    def max_tokens(self) -> int: return self._backend.max_tokens()
    def metadata(self) -> BackendMetadata:
        meta = self._backend.metadata()
        meta.name = f"cached({meta.name})"
        return meta
