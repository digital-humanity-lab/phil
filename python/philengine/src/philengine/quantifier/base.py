"""Quantifier protocol."""
from __future__ import annotations
from typing import Protocol, runtime_checkable
import numpy as np

@runtime_checkable
class Quantifier(Protocol):
    def quantify(self, texts: list[str]) -> np.ndarray: ...
    def feature_names(self) -> list[str]: ...
