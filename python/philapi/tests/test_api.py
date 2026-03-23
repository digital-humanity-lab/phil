"""Tests for philapi FastAPI application.

All tests run WITHOUT requiring ML models or external services.
"""

import pytest
from fastapi.testclient import TestClient

from philapi.app import app
from philapi.schemas import (
    CompareRequest, EmbedRequest, HealthResponse, SearchRequest,
)


@pytest.fixture
def client():
    return TestClient(app)


# ── Health endpoint ─────────────────────────────────────────────────

def test_health(client):
    """GET /health returns 200 with status 'ok'."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


# ── Schema validation ──────────────────────────────────────────────

def test_embed_request_schema():
    """EmbedRequest validates correctly."""
    req = EmbedRequest(texts=["hello", "world"])
    assert req.texts == ["hello", "world"]
    assert req.model == "default"

    req2 = EmbedRequest(texts=["test"], model="custom-model")
    assert req2.model == "custom-model"


def test_embed_request_validation():
    """EmbedRequest requires texts field."""
    with pytest.raises(Exception):
        EmbedRequest()  # type: ignore[call-arg]


def test_search_request_schema():
    """SearchRequest validates correctly."""
    req = SearchRequest(query="emptiness")
    assert req.query == "emptiness"
    assert req.top_k == 10
    assert req.traditions is None

    req2 = SearchRequest(query="仁", traditions=["Confucian"], top_k=5)
    assert req2.traditions == ["Confucian"]
    assert req2.top_k == 5


def test_compare_request_schema():
    """CompareRequest validates correctly."""
    req = CompareRequest(concept_a="ren", concept_b="ubuntu")
    assert req.concept_a == "ren"
    assert req.concept_b == "ubuntu"
    assert req.method == "hybrid"

    req2 = CompareRequest(concept_a="a", concept_b="b", method="semantic")
    assert req2.method == "semantic"


def test_health_response_schema():
    """HealthResponse schema validates."""
    resp = HealthResponse(status="ok", version="0.1.0")
    assert resp.status == "ok"
    assert resp.models_loaded == []

    resp2 = HealthResponse(
        status="ok", version="0.1.0",
        models_loaded=["model-a", "model-b"],
    )
    assert len(resp2.models_loaded) == 2
