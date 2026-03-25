"""Base protocol for embedding backends."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
import numpy as np

@dataclass
class BackendMetadata:
    name: str
    model_name: str
    dimensions: int
    max_tokens: int
    supports_batch: bool = True

@runtime_checkable
class EmbeddingBackend(Protocol):
    def encode(self, texts: list[str], **kwargs) -> np.ndarray: ...
    def dim(self) -> int: ...
    def max_tokens(self) -> int: ...
    def metadata(self) -> BackendMetadata: ...
