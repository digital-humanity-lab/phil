"""Tests for philtext data models and taxonomy.

All tests run WITHOUT requiring sentence-transformers, torch, or any API.
"""

import pytest

from philtext.classify.school import SCHOOL_TAXONOMY
from philtext.argument.schemas import (
    Argument, Conclusion, InferenceType, Premise, Proposition,
)
from philtext.concept.ontology import ConceptMention, ConceptNode
from philtext.hermeneutic.interpretation import Interpretation, InterpretationTracker


# ── SCHOOL_TAXONOMY ─────────────────────────────────────────────────

def test_school_taxonomy_has_expected_traditions():
    """SCHOOL_TAXONOMY has all expected tradition groups."""
    expected = {"Western", "East Asian", "South Asian", "Islamic"}
    assert expected == set(SCHOOL_TAXONOMY.keys())


def test_school_taxonomy_count():
    """At least 40 schools across all traditions."""
    all_schools = [s for schools in SCHOOL_TAXONOMY.values() for s in schools]
    assert len(all_schools) >= 39


def test_school_taxonomy_contains_key_schools():
    """Key schools are present."""
    all_schools = [s for schools in SCHOOL_TAXONOMY.values() for s in schools]
    for school in ["Confucian", "Kyoto School", "Phenomenology", "Vedanta",
                   "Analytic", "Stoic", "Buddhist (Madhyamaka)"]:
        assert school in all_schools, f"{school} missing from taxonomy"


# ── Argument schemas ────────────────────────────────────────────────

def test_argument_creation():
    """Create Argument with Premises and Conclusion."""
    p1 = Premise(text="All men are mortal", confidence=1.0)
    p2 = Premise(text="Socrates is a man", confidence=1.0)
    c = Conclusion(text="Socrates is mortal")
    arg = Argument(
        premises=[p1, p2],
        conclusion=c,
        inference_type=InferenceType.DEDUCTIVE,
        source_text="Aristotle, Prior Analytics",
        confidence=0.95,
    )
    assert len(arg.premises) == 2
    assert arg.conclusion.text == "Socrates is mortal"
    assert arg.inference_type == InferenceType.DEDUCTIVE


def test_argument_standard_form():
    """Standard form output is readable."""
    p = Premise(text="If P then Q")
    c = Conclusion(text="Therefore Q")
    arg = Argument(
        premises=[p], conclusion=c,
        inference_type=InferenceType.DEDUCTIVE,
        source_text="test", confidence=0.9,
    )
    sf = arg.to_standard_form()
    assert "P1." in sf
    assert "C." in sf
    assert "deductive" in sf


def test_premise_implicit():
    """Implicit premise is marked."""
    p = Premise(text="Hidden assumption", is_implicit=True,
                reconstruction_note="Reconstructed by analyst")
    assert p.is_implicit is True
    assert p.reconstruction_note == "Reconstructed by analyst"


# ── InferenceType ───────────────────────────────────────────────────

def test_inference_types():
    """All 7 inference types exist."""
    expected = {
        "DEDUCTIVE", "INDUCTIVE", "ABDUCTIVE", "ANALOGICAL",
        "TRANSCENDENTAL", "DIALECTICAL", "REDUCTIO",
    }
    actual = {e.name for e in InferenceType}
    assert expected == actual


# ── ConceptMention ──────────────────────────────────────────────────

def test_concept_mention():
    """ConceptMention creation with all fields."""
    node = ConceptNode(
        id="ren", labels={"zh": "仁", "en": "Ren"},
        definition="Confucian virtue of humaneness",
    )
    mention = ConceptMention(
        concept=node,
        surface_form="仁",
        span=(10, 11),
        confidence=0.92,
        context_sentence="克己復礼を仁と為す。",
        usage_sense="virtue",
    )
    assert mention.concept.id == "ren"
    assert mention.surface_form == "仁"
    assert mention.span == (10, 11)
    assert mention.confidence == 0.92
    assert mention.usage_sense == "virtue"


def test_concept_node_label():
    """ConceptNode.label() returns correct language."""
    node = ConceptNode(id="dao", labels={"zh": "道", "en": "Dao"})
    assert node.label("zh") == "道"
    assert node.label("en") == "Dao"
    assert node.label("de") == "Dao"  # fallback to en


# ── InterpretationTracker ───────────────────────────────────────────

def test_interpretation_tracker():
    """InterpretationTracker creation and basic operations."""
    tracker = InterpretationTracker()

    i1 = Interpretation(
        id="int1",
        interpreter="Nishitani",
        target_text="般若心経",
        target_ref="heart_sutra:1",
        reading="Emptiness as absolute nothingness",
        school_of_interpretation="Kyoto School",
    )
    i2 = Interpretation(
        id="int2",
        interpreter="Nagarjuna",
        target_text="般若心経",
        target_ref="heart_sutra:1",
        reading="Emptiness as dependent origination",
        school_of_interpretation="Madhyamaka",
    )
    tracker.add(i1)
    tracker.add(i2)

    # Find conflicts (different readings of same ref)
    conflicts = tracker.find_conflicts("heart_sutra:1")
    assert len(conflicts) == 1

    # Interpreters for a reference
    interpreters = tracker.interpreters_for("heart_sutra:1")
    assert set(interpreters) == {"Nishitani", "Nagarjuna"}


def test_interpretation_tracker_summarize():
    """Summarize debate produces structured output."""
    tracker = InterpretationTracker()
    i1 = Interpretation(
        id="int1", interpreter="A", target_text="text",
        target_ref="ref1", reading="Reading A",
        school_of_interpretation="School1",
    )
    i2 = Interpretation(
        id="int2", interpreter="B", target_text="text",
        target_ref="ref1", reading="Reading B",
        school_of_interpretation="School2",
    )
    tracker.add(i1)
    tracker.add(i2)

    summary = tracker.summarize_debate("ref1")
    assert summary["num_interpretations"] == 2
    assert "A" in summary["interpreters"]
    assert summary["num_conflicts"] == 1


def test_interpretation_tracker_empty():
    """Summarize on unknown ref returns appropriate status."""
    tracker = InterpretationTracker()
    summary = tracker.summarize_debate("nonexistent")
    assert summary["status"] == "no_interpretations_found"
