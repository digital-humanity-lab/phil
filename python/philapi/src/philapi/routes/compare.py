"""Compare endpoint."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends

from ..schemas import CompareRequest, CompareResponse
from ..dependencies import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()

# Path to the benchmark concept pairs YAML (used as fallback)
_BENCHMARK_PATH = (
    Path(__file__).resolve().parents[6]
    / "shared"
    / "benchmarks"
    / "concept_pairs_v1.yaml"
)


def _load_benchmark_pairs() -> list[dict]:
    """Load benchmark concept pairs from YAML file."""
    try:
        import yaml

        with open(_BENCHMARK_PATH) as f:
            data = yaml.safe_load(f)
        return data.get("pairs", [])
    except Exception:
        logger.warning("Could not load benchmark pairs from %s", _BENCHMARK_PATH)
        return []


def _find_benchmark_pair(
    concept_a: str, concept_b: str, pairs: list[dict]
) -> dict | None:
    """Find a matching benchmark pair by label or ID (order-insensitive)."""
    for pair in pairs:
        a_labels = {
            pair["concept_a"]["id"],
            pair["concept_a"]["label"],
            pair["concept_a"]["label"].lower(),
        }
        b_labels = {
            pair["concept_b"]["id"],
            pair["concept_b"]["label"],
            pair["concept_b"]["label"].lower(),
        }
        ca, cb = concept_a.lower(), concept_b.lower()
        if (ca in {s.lower() for s in a_labels} and cb in {s.lower() for s in b_labels}) or (
            cb in {s.lower() for s in a_labels} and ca in {s.lower() for s in b_labels}
        ):
            return pair
    return None


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return dot / (norm_a * norm_b)


@router.post("/compare", response_model=CompareResponse)
async def compare_concepts(req: CompareRequest, engine=Depends(get_engine)):
    """Compare two philosophical concepts and return similarity scores."""
    similarity = 0.0
    facet_scores: dict[str, float] = {}
    evidence: list[str] = []
    method = req.method

    # Try engine-based comparison
    try:
        if req.method in ("semantic", "hybrid"):
            embs = engine.encode([req.concept_a, req.concept_b])
            similarity = _cosine_similarity(embs[0], embs[1])
            evidence.append(f"Cosine similarity via {engine._model}: {similarity:.4f}")

        # Try faceted embedding if method is hybrid or faceted
        if req.method in ("hybrid", "faceted"):
            try:
                facet_a = engine.encode_faceted(
                    definition=req.concept_a,
                    usage=f"The concept of {req.concept_a} is used in philosophical discourse",
                    relational=f"{req.concept_a} relates to other concepts in tradition",
                )
                facet_b = engine.encode_faceted(
                    definition=req.concept_b,
                    usage=f"The concept of {req.concept_b} is used in philosophical discourse",
                    relational=f"{req.concept_b} relates to other concepts in tradition",
                )
                for facet_name in ("definition", "usage", "relational"):
                    vec_a = facet_a.facet(facet_name)
                    vec_b = facet_b.facet(facet_name)
                    facet_scores[facet_name] = round(
                        _cosine_similarity(vec_a, vec_b), 4
                    )
                evidence.append("Faceted embedding scores computed")
            except Exception:
                logger.debug("Faceted embedding failed, skipping", exc_info=True)

    except Exception:
        logger.warning(
            "Engine unavailable for compare, falling back to benchmark pairs",
            exc_info=True,
        )
        # Fallback: look up in benchmark pairs
        benchmark_pairs = _load_benchmark_pairs()
        match = _find_benchmark_pair(req.concept_a, req.concept_b, benchmark_pairs)
        if match is not None:
            similarity = match["expected_similarity"]
            evidence.append(
                f"Benchmark expected similarity: {similarity:.2f} "
                f"({match.get('scholarly_reference', 'n/a')})"
            )
            method = "benchmark_fallback"
        else:
            evidence.append(
                "No engine available and no benchmark match found; "
                "returning zero similarity"
            )
            method = "unavailable"

    return CompareResponse(
        similarity=round(similarity, 4),
        method=method,
        facet_scores=facet_scores,
        evidence=evidence,
    )
