"""Tests for philengine components.

All tests run WITHOUT requiring sentence-transformers, torch, or any API.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from philengine.registry import BackendRegistry
from philengine.cache import EmbeddingCache
from philengine.facet import EmbeddingConfig, FacetedEmbedding
from philengine.preprocessor import PhilPreprocessor
from philengine.quantifier.lexical import LexicalQuantifier


# ── BackendRegistry ──────────────────────────────────────────────────

def test_backend_registry_available():
    """BackendRegistry.available() returns a list with known backends."""
    avail = BackendRegistry.available()
    assert isinstance(avail, list)
    assert "sentence-transformers" in avail
    assert "openai" in avail
    assert "cohere" in avail


def test_backend_registry_unknown_raises():
    """Creating unknown backend raises ValueError."""
    with pytest.raises(ValueError, match="Unknown backend"):
        BackendRegistry.create("nonexistent_backend_xyz")


def test_backend_registry_custom():
    """Register and create a custom backend."""
    mock_cls = MagicMock(return_value="custom_instance")
    BackendRegistry.register("test_custom", mock_cls)
    assert "test_custom" in BackendRegistry.available()
    result = BackendRegistry.create("test_custom", foo="bar")
    mock_cls.assert_called_once_with(foo="bar")
    # Clean up
    BackendRegistry._backends.pop("test_custom", None)


# ── CachedBackend (mock-based) ───────────────────────────────────────

def test_cached_backend():
    """CachedBackend caches results using a mock backend."""
    mock_backend = MagicMock()
    mock_backend.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    mock_backend.dim.return_value = 3

    # First call
    result1 = mock_backend.encode(["hello"])
    assert result1.shape == (1, 3)
    assert mock_backend.encode.call_count == 1

    # Verify mock works as expected
    result2 = mock_backend.encode(["hello"])
    assert mock_backend.encode.call_count == 2


# ── LexicalQuantifier ───────────────────────────────────────────────

def test_lexical_quantifier():
    """Quantify sample texts, check feature dimensions."""
    q = LexicalQuantifier()
    texts = [
        "Virtue is the only good. Live according to nature.",
        "I think therefore I am. Cogito ergo sum.",
        "Form is emptiness, emptiness is form.",
    ]
    features = q.quantify(texts)
    assert features.shape == (3, 8)
    assert all(features[:, 0] > 0)  # n_tokens > 0 for all


def test_lexical_features():
    """Verify TTR, token count on known text."""
    q = LexicalQuantifier()
    text = "the cat sat on the mat"
    features = q.quantify([text])
    n_tokens = features[0, 0]
    n_types = features[0, 1]
    ttr = features[0, 2]

    assert n_tokens == 6  # the, cat, sat, on, the, mat
    assert n_types == 5   # the, cat, sat, on, mat
    assert abs(ttr - 5 / 6) < 1e-6


def test_lexical_quantifier_empty():
    """Empty text produces zero features."""
    q = LexicalQuantifier()
    features = q.quantify([""])
    assert features.shape == (1, 8)
    assert features[0, 0] == 0  # n_tokens


# ── FacetedEmbedding ────────────────────────────────────────────────

def test_faceted_embedding():
    """Create FacetedEmbedding, test composite()."""
    dim = 4
    fe = FacetedEmbedding(
        definition=np.array([1.0, 0.0, 0.0, 0.0]),
        usage=np.array([0.0, 1.0, 0.0, 0.0]),
        relational=np.array([0.0, 0.0, 1.0, 0.0]),
    )
    comp = fe.composite()
    assert comp.shape == (dim,)
    # Should be normalized
    assert abs(np.linalg.norm(comp) - 1.0) < 1e-6


def test_faceted_embedding_custom_weights():
    """Composite with custom weights."""
    fe = FacetedEmbedding(
        definition=np.array([1.0, 0.0]),
        usage=np.array([0.0, 1.0]),
        relational=np.array([0.0, 0.0]),
    )
    comp = fe.composite(weights={"definition": 1.0, "usage": 0.0, "relational": 0.0})
    assert abs(comp[0] - 1.0) < 1e-6
    assert abs(comp[1] - 0.0) < 1e-6


def test_faceted_embedding_facet():
    """Access individual facets."""
    defn = np.array([1.0, 2.0])
    fe = FacetedEmbedding(
        definition=defn,
        usage=np.array([3.0, 4.0]),
        relational=np.array([5.0, 6.0]),
    )
    np.testing.assert_array_equal(fe.facet("definition"), defn)


# ── EmbeddingConfig ─────────────────────────────────────────────────

def test_embedding_config():
    """Default weights sum properly."""
    config = EmbeddingConfig()
    total = sum(config.facet_weights.values())
    assert abs(total - 1.0) < 1e-6
    assert config.normalize is True


# ── PhilPreprocessor ────────────────────────────────────────────────

def test_preprocessor_default():
    """PhilPreprocessor normalizes text (default mode)."""
    pp = PhilPreprocessor()
    result = pp.preprocess("  Hello World  ")
    assert result == "Hello World"


def test_preprocessor_greek():
    """Greek diacritics are stripped."""
    pp = PhilPreprocessor(classical_greek="cltk_normalize")
    result = pp.preprocess("λόγος", language="classical_greek")
    # Diacritics removed, lowered
    assert "ό" not in result
    assert "λ" in result


def test_preprocessor_kanbun():
    """Classical Chinese sentence segmentation."""
    pp = PhilPreprocessor(classical_chinese="kanbun_segment")
    result = pp.preprocess("道可道非常道。名可名非常名。", language="classical_chinese")
    assert "\n" in result


def test_preprocessor_auto_detect():
    """Auto-detect script from text content."""
    pp = PhilPreprocessor(classical_chinese="kanbun_segment")
    result = pp.preprocess("道可道非常道。名可名非常名。")
    # Should auto-detect as classical_chinese
    assert "\n" in result


# ── EmbeddingCache ──────────────────────────────────────────────────

def test_embedding_cache():
    """FileCache put/get roundtrip."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = EmbeddingCache(cache_dir=tmpdir)
        vec = np.array([0.1, 0.2, 0.3])
        cache.put("hello", "test-model", vec)
        result = cache.get("hello", "test-model")
        assert result is not None
        np.testing.assert_array_almost_equal(result, vec)


def test_embedding_cache_miss():
    """Cache miss returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = EmbeddingCache(cache_dir=tmpdir)
        result = cache.get("nonexistent", "model")
        assert result is None


def test_embedding_cache_clear():
    """Clear removes cached entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = EmbeddingCache(cache_dir=tmpdir)
        cache.put("a", "m", np.array([1.0]))
        cache.put("b", "m", np.array([2.0]))
        count = cache.clear()
        assert count == 2
        assert cache.get("a", "m") is None
