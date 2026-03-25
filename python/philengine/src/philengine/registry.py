"""Backend registry for philengine."""
from __future__ import annotations
from typing import Any

class BackendRegistry:
    _backends: dict[str, type] = {}

    @classmethod
    def register(cls, name: str, backend_cls: type) -> None:
        cls._backends[name] = backend_cls

    @classmethod
    def create(cls, name: str, **kwargs) -> Any:
        if name == "sentence-transformers":
            from .backend.sentence_transformers import SentenceTransformersBackend
            return SentenceTransformersBackend(model_name=kwargs.get("model", ""), **{k: v for k, v in kwargs.items() if k != "model"})
        elif name == "openai":
            from .backend.openai import OpenAIBackend
            return OpenAIBackend(model_name=kwargs.get("model", "text-embedding-3-large"))
        elif name == "cohere":
            from .backend.cohere import CohereBackend
            return CohereBackend(model_name=kwargs.get("model", "embed-multilingual-v3.0"))
        elif name in cls._backends:
            return cls._backends[name](**kwargs)
        else:
            raise ValueError(f"Unknown backend: {name}. Available: sentence-transformers, openai, cohere, {list(cls._backends.keys())}")

    @classmethod
    def available(cls) -> list[str]:
        return ["sentence-transformers", "openai", "cohere"] + list(cls._backends.keys())
