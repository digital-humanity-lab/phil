"""Tests for philbench pipeline and result types.

All tests run WITHOUT requiring sentence-transformers, torch, or any API.
"""

from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from philbench.results import ComparisonResult, ExplorationResult, SearchResults


# ── SearchResults ───────────────────────────────────────────────────

def test_search_results_repr():
    """SearchResults has meaningful __repr__."""
    sr = SearchResults(
        query="emptiness",
        results=[
            {"label": "Sunyata", "similarity": 0.95, "tradition": "Buddhist"},
            {"label": "Wu", "similarity": 0.72, "tradition": "Daoist"},
        ],
        model="test-model",
    )
    text = repr(sr)
    assert "emptiness" in text
    assert "2 results" in text
    assert "Sunyata" in text
    assert "0.950" in text


def test_search_results_empty():
    """Empty SearchResults repr is still meaningful."""
    sr = SearchResults(query="nothing")
    text = repr(sr)
    assert "nothing" in text
    assert "0 results" in text


# ── ComparisonResult ────────────────────────────────────────────────

def test_comparison_result_repr():
    """ComparisonResult has meaningful __repr__."""
    cr = ComparisonResult(
        concept_a="仁",
        concept_b="Ubuntu",
        similarity=0.78,
        method="hybrid",
        facet_scores={"semantic": 0.85, "structural": 0.70},
    )
    text = repr(cr)
    assert "仁" in text
    assert "Ubuntu" in text
    assert "0.780" in text
    assert "hybrid" in text
    assert "semantic" in text


# ── PhilPipeline ────────────────────────────────────────────────────

def _make_corpus():
    from philcore.corpus import PhilCorpus
    return PhilCorpus(
        assay=np.zeros((2, 3)),
        concept_data=pd.DataFrame({"id": ["c1", "c2"]}),
        text_data=pd.DataFrame({"id": ["t1", "t2", "t3"]}),
    )


def test_pipeline_creation():
    """PhilPipeline with a PhilCorpus creates object without error."""
    from philbench.pipeline import PhilPipeline
    corpus = _make_corpus()
    pipe = PhilPipeline(source=corpus)
    assert pipe is not None


def test_pipeline_search_chaining():
    """Pipeline search method returns self for chaining."""
    from philbench.pipeline import PhilPipeline
    corpus = _make_corpus()
    pipe = PhilPipeline(source=corpus)
    result = pipe.search(concept="emptiness", top_k=5)
    assert result is pipe  # returns self


def test_pipeline_compare_chaining():
    """Pipeline compare method returns self for chaining."""
    from philbench.pipeline import PhilPipeline
    corpus = _make_corpus()
    pipe = PhilPipeline(source=corpus)
    result = pipe.compare("ren", "ubuntu")
    assert result is pipe


# ── Verbs ───────────────────────────────────────────────────────────

def test_verbs_exist():
    """All 7 verbs are importable."""
    from philbench.verbs import read, embed, search, compare, explore, annotate, quantify
    assert callable(read)
    assert callable(embed)
    assert callable(search)
    assert callable(compare)
    assert callable(explore)
    assert callable(annotate)
    assert callable(quantify)


def test_verb_search_returns_results():
    """search() returns SearchResults."""
    from philbench.verbs import search
    result = search("test query")
    assert isinstance(result, SearchResults)
    assert result.query == "test query"


def test_verb_compare_returns_result():
    """compare() returns ComparisonResult."""
    from philbench.verbs import compare
    result = compare("concept_a", "concept_b", method="semantic")
    assert isinstance(result, ComparisonResult)
    assert result.concept_a == "concept_a"
    # Method may be "local_engine" or "benchmark_fallback" depending on
    # whether PhilEngine is available; just check it is set.
    assert isinstance(result.method, str)
    assert len(result.method) > 0


def test_verb_explore_returns_result():
    """explore() returns ExplorationResult."""
    from philbench.verbs import explore
    result = explore("test", traditions=["Western"])
    assert isinstance(result, ExplorationResult)
    assert result.traditions == ["Western"]
