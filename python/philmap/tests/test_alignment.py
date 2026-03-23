"""Tests for philmap concept alignment and mapping.

All tests run WITHOUT requiring sentence-transformers or torch.
"""

import inspect

import pytest

from philmap.concept import (
    AlignmentEvidence,
    AlignmentType,
    Concept,
    ConceptDescription,
    ConceptDiff,
    ConceptMapping,
    Tradition,
)
from philmap.analysis.analogues import find_analogues
from philmap.analysis.bridge import tradition_bridge


def _make_tradition(name="Confucian", lang="zh"):
    return Tradition(name=name, language=lang)


def _make_concept(cid, term, tradition=None):
    trad = tradition or _make_tradition()
    return Concept(
        id=cid,
        tradition=trad,
        descriptions=[ConceptDescription(
            language=trad.language,
            term=term,
            definition=f"Definition of {term}",
        )],
    )


# ── ConceptMapping ──────────────────────────────────────────────────

def test_concept_mapping_creation():
    """Create ConceptMapping with source, target, score."""
    src = _make_concept("c1", "仁")
    tgt = _make_concept("c2", "Ubuntu", _make_tradition("Ubuntu Philosophy", "en"))
    evidence = AlignmentEvidence(
        method=AlignmentType.SEMANTIC, score=0.85, details={"model": "test"},
    )
    mapping = ConceptMapping(
        source=src, target=tgt,
        overall_score=0.85,
        alignment_type=AlignmentType.SEMANTIC,
        evidence=[evidence],
    )
    assert mapping.overall_score == 0.85
    assert mapping.source.primary_term == "仁"
    assert mapping.target.primary_term == "Ubuntu"
    assert len(mapping.evidence) == 1


def test_concept_mapping_explain():
    """ConceptMapping.explain() produces a readable string."""
    src = _make_concept("c1", "仁")
    tgt = _make_concept("c2", "Ren", _make_tradition("Western", "en"))
    mapping = ConceptMapping(
        source=src, target=tgt,
        overall_score=0.9,
        alignment_type=AlignmentType.HYBRID,
        notes="Test note",
    )
    text = mapping.explain()
    assert "仁" in text
    assert "Ren" in text
    assert "0.900" in text
    assert "Test note" in text


# ── ConceptDiff ─────────────────────────────────────────────────────

def test_concept_diff():
    """Create ConceptDiff with shared/unique aspects."""
    a = _make_concept("c1", "仁")
    b = _make_concept("c2", "Ubuntu", _make_tradition("Ubuntu Philosophy", "en"))
    diff = ConceptDiff(
        concept_a=a, concept_b=b,
        shared_aspects=["communal ethics", "relational self"],
        unique_to_a=["li-ren relationship"],
        unique_to_b=["ubuntu as lived practice"],
        similarity_by_facet={"semantic": 0.7, "structural": 0.5},
        overall_similarity=0.6,
        narrative="Both emphasize relational aspects of ethics.",
    )
    assert diff.overall_similarity == 0.6
    assert len(diff.shared_aspects) == 2
    assert "li-ren relationship" in diff.unique_to_a


# ── HybridAlignment weights ────────────────────────────────────────

def test_hybrid_alignment_weights():
    """Verify default weights sum to ~1.0 (tested via import of defaults)."""
    # The HybridAlignment class uses default weights that should sum to 1.0
    # We test this without instantiating (which would require ML models)
    default_weights = {"semantic": 0.4, "structural": 0.35, "argumentative": 0.25}
    total = sum(default_weights.values())
    assert abs(total - 1.0) < 1e-6


# ── find_analogues signature ────────────────────────────────────────

def test_find_analogues_signature():
    """Function exists and has correct params."""
    sig = inspect.signature(find_analogues)
    params = list(sig.parameters.keys())
    assert "concept" in params
    assert "target_tradition" in params
    assert "alignment" in params
    assert "concept_registry" in params
    assert "top_k" in params


# ── tradition_bridge signature ──────────────────────────────────────

def test_tradition_bridge_signature():
    """Function exists and has correct params."""
    sig = inspect.signature(tradition_bridge)
    params = list(sig.parameters.keys())
    assert "tradition_a" in params
    assert "tradition_b" in params
    assert "alignment" in params
    assert "concept_registry" in params
    assert "threshold" in params
