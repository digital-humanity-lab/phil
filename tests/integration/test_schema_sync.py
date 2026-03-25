"""Integration tests: verify JSON Schemas are valid and in sync with Python models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "shared" / "schemas"

SCHEMA_FILES = sorted(SCHEMA_DIR.glob("*.schema.json"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_schema(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _top_level_property_names(schema: dict) -> set[str]:
    """Return the set of top-level property names defined in a schema."""
    return set(schema.get("properties", {}).keys())


# ---------------------------------------------------------------------------
# 1. Every *.schema.json is valid JSON and has the basic JSON Schema keys
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("schema_path", SCHEMA_FILES, ids=lambda p: p.name)
def test_schema_is_valid_json_schema(schema_path: Path) -> None:
    """Each schema must be parseable JSON and declare itself as a JSON Schema."""
    schema = _load_schema(schema_path)

    assert "$schema" in schema, f"{schema_path.name} missing '$schema' keyword"
    assert "type" in schema or "items" in schema, (
        f"{schema_path.name} missing root 'type' or 'items'"
    )
    # If it is an object schema it should have properties
    if schema.get("type") == "object":
        assert "properties" in schema, (
            f"{schema_path.name} is type=object but has no 'properties'"
        )


# ---------------------------------------------------------------------------
# 2. concept.schema.json fields ↔ philcore Concept model
# ---------------------------------------------------------------------------

def test_concept_schema_fields_match_model() -> None:
    """Core concept.schema.json fields must have counterparts in Concept."""
    from philcore.models.concept import Concept

    schema = _load_schema(SCHEMA_DIR / "concept.schema.json")
    schema_props = _top_level_property_names(schema)

    # The Concept pydantic model field names
    model_fields = set(Concept.model_fields.keys())

    # Schema has 'id' → model has 'id'
    assert "id" in schema_props, "Schema missing 'id'"
    assert "id" in model_fields, "Model missing 'id'"

    # Schema has 'labels' → model has 'labels'
    assert "labels" in schema_props, "Schema missing 'labels'"
    assert "labels" in model_fields, "Model missing 'labels'"

    # Schema has 'tradition' → model has 'tradition_ids'
    assert "tradition" in schema_props, "Schema missing 'tradition'"
    assert "tradition_ids" in model_fields, (
        "Model missing 'tradition_ids' (maps to schema 'tradition')"
    )

    # Schema has 'definition' → model has 'definition'
    assert "definition" in schema_props, "Schema missing 'definition'"
    assert "definition" in model_fields, "Model missing 'definition'"


# ---------------------------------------------------------------------------
# 3. alignment_result.schema.json required fields exist
# ---------------------------------------------------------------------------

def test_alignment_result_schema_fields_exist() -> None:
    """alignment_result.schema.json must define the expected fields."""
    schema = _load_schema(SCHEMA_DIR / "alignment_result.schema.json")
    props = _top_level_property_names(schema)

    expected = {"concept_a_id", "concept_b_id", "method", "similarity"}
    missing = expected - props
    assert not missing, f"alignment_result.schema.json missing fields: {missing}"

    # required list should contain the expected fields
    required = set(schema.get("required", []))
    assert expected <= required, (
        f"alignment_result required mismatch: expected {expected}, got {required}"
    )


# ---------------------------------------------------------------------------
# 4. concept_spans.schema.json required fields exist
# ---------------------------------------------------------------------------

def test_concept_spans_schema_fields_exist() -> None:
    """concept_spans.schema.json must define the expected item fields."""
    schema = _load_schema(SCHEMA_DIR / "concept_spans.schema.json")

    # This is an array schema; check item properties
    if schema.get("type") == "array":
        item_props = set(schema["items"].get("properties", {}).keys())
    else:
        item_props = _top_level_property_names(schema)

    expected = {"text_id", "start", "end", "concept_id"}
    missing = expected - item_props
    assert not missing, f"concept_spans.schema.json missing fields: {missing}"


# ---------------------------------------------------------------------------
# 5. phil_corpus.schema.json required fields exist
# ---------------------------------------------------------------------------

def test_phil_corpus_schema_fields_exist() -> None:
    """phil_corpus.schema.json must define the expected fields."""
    schema = _load_schema(SCHEMA_DIR / "phil_corpus.schema.json")
    props = _top_level_property_names(schema)

    expected = {"layers", "segment_data", "text_metadata"}
    missing = expected - props
    assert not missing, f"phil_corpus.schema.json missing fields: {missing}"

    required = set(schema.get("required", []))
    assert expected <= required, (
        f"phil_corpus required mismatch: expected {expected}, got {required}"
    )
