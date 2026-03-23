"""Faceted embeddings for philosophical concepts."""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

@dataclass
class EmbeddingConfig:
    model_name: str = "intfloat/multilingual-e5-large-instruct"
    facet_weights: dict[str, float] = field(default_factory=lambda: {
        "definition": 0.5, "usage": 0.3, "relational": 0.2})
    instruction_prefix: str = "query: "
    max_seq_length: int = 512
    normalize: bool = True

@dataclass
class FacetedEmbedding:
    definition: np.ndarray
    usage: np.ndarray
    relational: np.ndarray
    config: EmbeddingConfig = field(default_factory=EmbeddingConfig)

    def composite(self, weights: dict[str, float] | None = None) -> np.ndarray:
        w = weights or self.config.facet_weights
        vec = (w.get("definition", 0.5) * self.definition +
               w.get("usage", 0.3) * self.usage +
               w.get("relational", 0.2) * self.relational)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 1e-9 else vec

    def facet(self, name: str) -> np.ndarray:
        if name == "composite": return self.composite()
        return getattr(self, name)
