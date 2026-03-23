"""OpenAI embedding backend."""
from __future__ import annotations
import numpy as np
from .base import BackendMetadata

class OpenAIBackend:
    def __init__(self, model_name: str = "text-embedding-3-large"):
        self._model_name = model_name
        self._client = None
        self._dim = 3072 if "large" in model_name else 1536

    def _load_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("Install openai: pip install philengine[openai]")
            self._client = OpenAI()

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        self._load_client()
        resp = self._client.embeddings.create(input=texts, model=self._model_name)
        return np.array([d.embedding for d in resp.data])

    def dim(self) -> int: return self._dim
    def max_tokens(self) -> int: return 8191
    def metadata(self) -> BackendMetadata:
        return BackendMetadata(name="openai", model_name=self._model_name,
                               dimensions=self._dim, max_tokens=8191)
