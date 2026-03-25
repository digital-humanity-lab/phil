"""Cohere embedding backend."""
from __future__ import annotations
import numpy as np
from .base import BackendMetadata

class CohereBackend:
    def __init__(self, model_name: str = "embed-multilingual-v3.0"):
        self._model_name = model_name
        self._client = None

    def _load_client(self):
        if self._client is None:
            try:
                import cohere
            except ImportError:
                raise ImportError("Install cohere: pip install philengine[cohere]")
            self._client = cohere.ClientV2()

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        self._load_client()
        resp = self._client.embed(texts=texts, model=self._model_name,
                                   input_type="search_document", embedding_types=["float"])
        return np.array(resp.embeddings.float)

    def dim(self) -> int: return 1024
    def max_tokens(self) -> int: return 512
    def metadata(self) -> BackendMetadata:
        return BackendMetadata(name="cohere", model_name=self._model_name,
                               dimensions=1024, max_tokens=512)
