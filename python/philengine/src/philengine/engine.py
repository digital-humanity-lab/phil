"""PhilEngine: unified text quantification API."""
from __future__ import annotations
from typing import Any
import numpy as np
from .facet import EmbeddingConfig, FacetedEmbedding
from .registry import BackendRegistry

class PhilEngine:
    def __init__(self, backend: str = "sentence-transformers",
                 model: str = "intfloat/multilingual-e5-large-instruct", **kwargs):
        self._backend_name = backend
        self._model = model
        self._backend = BackendRegistry.create(backend, model=model, **kwargs)
        self._config = EmbeddingConfig(model_name=model)

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        return self._backend.encode(texts, **kwargs)

    def similarity(self, text_a: str, text_b: str) -> float:
        embs = self.encode([text_a, text_b])
        return float(np.dot(embs[0], embs[1]))

    def encode_faceted(self, definition: str, usage: str, relational: str) -> FacetedEmbedding:
        embs = self.encode([definition, usage, relational])
        return FacetedEmbedding(
            definition=embs[0], usage=embs[1], relational=embs[2],
            config=self._config)

    @property
    def dim(self) -> int:
        return self._backend.dim()

    def __repr__(self) -> str:
        return f"PhilEngine(backend={self._backend_name!r}, model={self._model!r})"
