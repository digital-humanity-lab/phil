"""Tests for philcore data models."""

import numpy as np
import pandas as pd
import pytest

from philcore.models.concept import Concept, ConceptLabel, FormalProperty, TemporalContext
from philcore.corpus import PhilCorpus
from philcore.spans import ConceptSpans
from philcore.collection import PhilCollection


# ── Concept ──────────────────────────────────────────────────────────

def test_concept_creation():
    """Create Concept with labels, verify fields."""
    c = Concept(
        labels=[
            ConceptLabel(text="仁", lang="zh", is_primary=True),
            ConceptLabel(text="Ren", lang="en"),
        ],
        definition="Confucian virtue of humaneness",
        tradition_ids=["confucian"],
    )
    assert c.primary_label.text == "仁"
    assert c.primary_label.lang == "zh"
    assert c.label_in("en") == "Ren"
    assert c.label_in("de") is None
    assert c.definition == "Confucian virtue of humaneness"
    assert c.tradition_ids == ["confucian"]
    assert c.id.startswith("philcore:concept/")


def test_concept_serialization():
    """to_dict() / from_dict() roundtrip via model_dump / model_validate."""
    c = Concept(
        labels=[ConceptLabel(text="Dasein", lang="de", is_primary=True)],
        definition="Being-there",
        thinker_ids=["heidegger"],
    )
    d = c.model_dump()
    c2 = Concept.model_validate(d)
    assert c2.primary_label.text == "Dasein"
    assert c2.definition == "Being-there"
    assert c2.thinker_ids == ["heidegger"]


# ── PhilCorpus ───────────────────────────────────────────────────────

def _make_corpus(n_concepts=3, n_texts=4):
    assay = np.random.rand(n_concepts, n_texts)
    concept_data = pd.DataFrame({"concept_id": [f"c{i}" for i in range(n_concepts)]})
    text_data = pd.DataFrame({"text_id": [f"t{j}" for j in range(n_texts)]})
    return PhilCorpus(assay=assay, concept_data=concept_data, text_data=text_data)


def test_phil_corpus_creation():
    """Create PhilCorpus with assay, concept_data, text_data."""
    corpus = _make_corpus(3, 4)
    assert corpus.n_concepts == 3
    assert corpus.n_texts == 4
    assert corpus.shape == (3, 4)


def test_phil_corpus_creation_dimension_mismatch():
    """Dimension mismatch raises ValueError."""
    with pytest.raises(ValueError, match="concept_data"):
        PhilCorpus(
            assay=np.zeros((3, 4)),
            concept_data=pd.DataFrame({"x": [1, 2]}),  # wrong size
            text_data=pd.DataFrame({"y": range(4)}),
        )


def test_phil_corpus_subset():
    """Subsetting with row/column indices."""
    corpus = _make_corpus(5, 6)
    sub = corpus.subset_concepts([0, 2])
    assert sub.n_concepts == 2
    assert sub.n_texts == 6

    sub2 = corpus.subset_texts([1, 3, 5])
    assert sub2.n_concepts == 5
    assert sub2.n_texts == 3


# ── ConceptSpans ─────────────────────────────────────────────────────

def _make_spans():
    df = pd.DataFrame({
        "text_id": ["t1", "t1", "t2", "t2"],
        "concept_id": ["ren", "li", "ren", "dao"],
        "start": [0, 10, 5, 20],
        "end": [3, 15, 8, 25],
    })
    return ConceptSpans(spans=df)


def test_concept_spans_creation():
    """Create ConceptSpans and check basic properties."""
    cs = _make_spans()
    assert len(cs) == 4
    assert cs.n_spans == 4
    assert set(cs.text_ids) == {"t1", "t2"}
    assert set(cs.concept_ids) == {"ren", "li", "dao"}


def test_concept_spans_filter_by_concept():
    """Filter spans by concept_id."""
    cs = _make_spans()
    ren_spans = cs.by_concept("ren")
    assert ren_spans.n_spans == 2
    assert all(cid == "ren" for cid in ren_spans.spans["concept_id"])


def test_concept_spans_filter_by_text():
    """Filter spans by text_id (analogous to filter_by_interpretation)."""
    cs = _make_spans()
    t1_spans = cs.by_text("t1")
    assert t1_spans.n_spans == 2


def test_concept_spans_missing_columns():
    """Missing required columns raises ValueError."""
    with pytest.raises(ValueError, match="missing columns"):
        ConceptSpans(spans=pd.DataFrame({"text_id": ["t1"], "start": [0]}))


# ── PhilCollection ───────────────────────────────────────────────────

def test_phil_collection():
    """Create PhilCollection with multiple corpora."""
    c1 = _make_corpus(3, 4)
    c2 = _make_corpus(5, 4)

    coll = PhilCollection()
    coll.add_corpus("counts", c1)
    coll.add_corpus("tfidf", c2)

    assert len(coll) == 2
    assert "counts" in coll
    assert coll.assay_names == ["counts", "tfidf"]
    assert coll["counts"].n_concepts == 3
    assert coll["tfidf"].n_concepts == 5


def test_phil_collection_dimension_mismatch():
    """Adding corpus with wrong text dimension raises ValueError."""
    c1 = _make_corpus(3, 4)
    c2 = _make_corpus(3, 5)  # different n_texts

    coll = PhilCollection()
    coll.add_corpus("a", c1)
    with pytest.raises(ValueError):
        coll.add_corpus("b", c2)
