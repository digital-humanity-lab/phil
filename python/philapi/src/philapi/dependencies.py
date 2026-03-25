"""Dependency injection for FastAPI."""
from __future__ import annotations
from functools import lru_cache
from philengine import PhilEngine

@lru_cache(maxsize=1)
def get_engine() -> PhilEngine:
    return PhilEngine()
