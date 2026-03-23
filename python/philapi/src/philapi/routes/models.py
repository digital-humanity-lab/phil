"""Models listing endpoint."""
from __future__ import annotations

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# Default model metadata for known backends
_MODEL_METADATA: dict[str, dict] = {
    "sentence-transformers": {
        "name": "sentence-transformers",
        "default_model": "intfloat/multilingual-e5-large-instruct",
        "dimensions": 1024,
        "max_seq_length": 512,
        "languages": ["multilingual"],
        "description": "Multilingual E5 via sentence-transformers (local)",
    },
    "openai": {
        "name": "openai",
        "default_model": "text-embedding-3-large",
        "dimensions": 3072,
        "max_seq_length": 8191,
        "languages": ["multilingual"],
        "description": "OpenAI text embedding API",
    },
    "cohere": {
        "name": "cohere",
        "default_model": "embed-multilingual-v3.0",
        "dimensions": 1024,
        "max_seq_length": 512,
        "languages": ["multilingual"],
        "description": "Cohere multilingual embedding API",
    },
}


@router.get("/models")
async def list_models():
    """Return available embedding backends with metadata."""
    try:
        from philengine.registry import BackendRegistry

        available = BackendRegistry.available()
    except Exception:
        logger.warning("Could not query BackendRegistry", exc_info=True)
        available = list(_MODEL_METADATA.keys())

    backends = []
    for name in available:
        if name in _MODEL_METADATA:
            backends.append(_MODEL_METADATA[name])
        else:
            # Custom-registered backend with minimal info
            backends.append(
                {
                    "name": name,
                    "default_model": "unknown",
                    "dimensions": -1,
                    "description": "Custom-registered backend",
                }
            )

    return {"backends": backends}
