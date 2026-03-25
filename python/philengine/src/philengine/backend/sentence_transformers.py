"""Sentence-transformers backend."""
from __future__ import annotations
import numpy as np
from .base import BackendMetadata, EmbeddingBackend

class SentenceTransformersBackend:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large-instruct",
                 instruction_prefix: str = "query: "):
        self._model_name = model_name
        self._instruction_prefix = instruction_prefix
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError("Install sentence-transformers: pip install philengine[st]")
            self._model = SentenceTransformer(self._model_name)

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        self._load_model()
        prefixed = [self._instruction_prefix + t for t in texts]
        return self._model.encode(prefixed, normalize_embeddings=True, **kwargs)

    def dim(self) -> int:
        self._load_model()
        return self._model.get_sentence_embedding_dimension()

    def max_tokens(self) -> int:
        return 512

    def metadata(self) -> BackendMetadata:
        return BackendMetadata(
            name="sentence-transformers", model_name=self._model_name,
            dimensions=self.dim(), max_tokens=self.max_tokens())
