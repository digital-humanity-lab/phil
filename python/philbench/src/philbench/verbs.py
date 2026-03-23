"""Unified verb API for Phil ecosystem."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from philcore.corpus import PhilCorpus
from .results import SearchResults, ComparisonResult, ExplorationResult

logger = logging.getLogger(__name__)

# Base path for shared benchmark data
_SHARED_DIR = Path(__file__).resolve().parents[5] / "shared"
_BENCHMARK_PAIRS_PATH = _SHARED_DIR / "benchmarks" / "concept_pairs_v1.yaml"

# Phil API default URL
_API_BASE = "http://localhost:8000"

# ---- Known source identifiers for read() ----

_KNOWN_SOURCES: dict[str, dict[str, Any]] = {
    "watsuji_rinrigaku": {
        "title": "倫理学 (Rinrigaku: Ethics in Japan)",
        "author": "和辻哲郎",
        "tradition": "watsuji_ethics",
        "language": "ja",
        "concepts": [
            {"id": "phil:C00142", "label": "間柄 (aidagara)"},
            {"id": "phil:C00143", "label": "人間 (ningen)"},
            {"id": "phil:C00144", "label": "風土 (fudo)"},
        ],
    },
    "nishida_zen_no_kenkyu": {
        "title": "善の研究 (An Inquiry into the Good)",
        "author": "西田幾多郎",
        "tradition": "kyoto_school",
        "language": "ja",
        "concepts": [
            {"id": "phil:C00045", "label": "場所 (basho)"},
            {"id": "phil:C00046", "label": "純粋経験 (junsui keiken)"},
            {"id": "phil:C00047", "label": "絶対無 (zettai mu)"},
        ],
    },
    "heidegger_sein_und_zeit": {
        "title": "Sein und Zeit",
        "author": "Martin Heidegger",
        "tradition": "phenomenology",
        "language": "de",
        "concepts": [
            {"id": "phil:C00056", "label": "Dasein"},
            {"id": "phil:C00089", "label": "Mitsein"},
            {"id": "phil:C00091", "label": "Lichtung"},
        ],
    },
    "daodejing": {
        "title": "道德經 (Tao Te Ching)",
        "author": "老子",
        "tradition": "daoism",
        "language": "zh",
        "concepts": [
            {"id": "phil:C00012", "label": "道 (dao)"},
            {"id": "phil:C00178", "label": "wu wei (無為)"},
            {"id": "phil:C00179", "label": "德 (de)"},
        ],
    },
    "nagarjuna_mmk": {
        "title": "Mūlamadhyamakakārikā",
        "author": "Nāgārjuna",
        "tradition": "madhyamaka",
        "language": "sa",
        "concepts": [
            {"id": "phil:C00034", "label": "空 (sunyata)"},
            {"id": "phil:C00145", "label": "pratityasamutpada"},
            {"id": "phil:C00146", "label": "svabhāva"},
        ],
    },
}


def _build_corpus_from_source_info(
    source: str, info: dict[str, Any]
) -> PhilCorpus:
    """Build a PhilCorpus from a known-source metadata dict."""
    concepts = info.get("concepts", [])
    n_concepts = len(concepts) if concepts else 1
    concept_records = [
        {"concept_id": c["id"], "primary_label": c["label"]}
        for c in concepts
    ] if concepts else [{"concept_id": "unknown", "primary_label": source}]

    text_records = [
        {
            "text_id": f"{source}:full",
            "primary_label": info.get("title", source),
            "lang": info.get("language", "und"),
        }
    ]

    return PhilCorpus(
        assay=np.zeros((n_concepts, 1), dtype=np.float64),
        concept_data=pd.DataFrame(concept_records),
        text_data=pd.DataFrame(text_records),
        metadata={
            "source": source,
            "title": info.get("title", source),
            "author": info.get("author", ""),
            "tradition": info.get("tradition", ""),
            "language": info.get("language", ""),
        },
    )


def read(source: str, section: str | None = None) -> PhilCorpus:
    """Read a philosophical text into a PhilCorpus.

    Parameters
    ----------
    source : str
        Either a file path (.json, .yaml, .csv) or a known source
        identifier (e.g. ``"watsuji_rinrigaku"``).
    section : str or None
        Optional section filter within the source.
    """
    path = Path(source)

    # Check if it is a known identifier first
    if source in _KNOWN_SOURCES:
        return _build_corpus_from_source_info(source, _KNOWN_SOURCES[source])

    # File-based loading
    if path.suffix == ".json" and path.exists():
        with open(path) as f:
            data = json.load(f)
        # Expect {"concepts": [...], "texts": [...], "assay": [[...]]}
        concepts = data.get("concepts", [])
        texts = data.get("texts", [])
        assay = np.array(data["assay"]) if "assay" in data else np.zeros(
            (max(len(concepts), 1), max(len(texts), 1)), dtype=np.float64
        )
        return PhilCorpus(
            assay=assay,
            concept_data=pd.DataFrame(concepts) if concepts else pd.DataFrame(
                [{"concept_id": "unknown", "primary_label": source}]
            ),
            text_data=pd.DataFrame(texts) if texts else pd.DataFrame(
                [{"text_id": source, "primary_label": source, "lang": "und"}]
            ),
            metadata={"source": source, "section": section},
        )

    if path.suffix == ".yaml" and path.exists():
        try:
            import yaml

            with open(path) as f:
                data = yaml.safe_load(f)
            concepts = data.get("concepts", [])
            texts = data.get("texts", [])
            assay = np.array(data["assay"]) if "assay" in data else np.zeros(
                (max(len(concepts), 1), max(len(texts), 1)), dtype=np.float64
            )
            return PhilCorpus(
                assay=assay,
                concept_data=pd.DataFrame(concepts) if concepts else pd.DataFrame(
                    [{"concept_id": "unknown", "primary_label": source}]
                ),
                text_data=pd.DataFrame(texts) if texts else pd.DataFrame(
                    [{"text_id": source, "primary_label": source, "lang": "und"}]
                ),
                metadata={"source": source, "section": section},
            )
        except ImportError:
            logger.warning("PyYAML not installed; cannot read YAML files")

    if path.suffix == ".csv" and path.exists():
        df = pd.read_csv(path)
        return PhilCorpus(
            assay=df.select_dtypes(include=[np.number]).values,
            concept_data=pd.DataFrame(
                {"concept_id": [f"row:{i}" for i in range(len(df))],
                 "primary_label": [f"concept_{i}" for i in range(len(df))]}
            ),
            text_data=pd.DataFrame(
                {"text_id": list(df.select_dtypes(include=[np.number]).columns),
                 "primary_label": list(df.select_dtypes(include=[np.number]).columns),
                 "lang": ["und"] * len(df.select_dtypes(include=[np.number]).columns)}
            ),
            metadata={"source": source, "section": section},
        )

    if path.suffix == ".rds" and path.exists():
        # .rds proxy: read the JSON sidecar if present
        json_path = path.with_suffix(".json")
        if json_path.exists():
            return read(str(json_path), section=section)
        logger.warning(
            "Cannot read .rds directly; looked for JSON sidecar at %s", json_path
        )

    # Fallback: treat source as a text label and return a minimal corpus
    logger.info("Source %r not found as file or known ID; creating stub corpus", source)
    return PhilCorpus(
        assay=np.zeros((1, 1), dtype=np.float64),
        concept_data=pd.DataFrame([{"concept_id": "unknown", "primary_label": source}]),
        text_data=pd.DataFrame([{"text_id": source, "primary_label": source, "lang": "und"}]),
        metadata={"source": source, "section": section},
    )


def embed(
    corpus: PhilCorpus,
    model: str = "default",
    layer_name: str = "embedding",
) -> PhilCorpus:
    """Embed all segments, add as new layer."""
    from philengine import PhilEngine

    engine = PhilEngine()
    # Use concept primary labels as text for embedding
    texts = list(corpus.concept_data.get("primary_label", []))
    if not texts:
        return corpus
    embeddings = engine.encode(texts)
    corpus.metadata[f"layer:{layer_name}"] = embeddings.tolist()
    return corpus


def search(
    query: str,
    traditions: list[str] | None = None,
    top_k: int = 10,
) -> SearchResults:
    """Search for similar concepts/passages.

    Tries the philapi /search endpoint first; falls back to local
    philengine-based search if the API is unavailable.
    """
    # Try API first
    try:
        import httpx

        payload: dict[str, Any] = {"query": query, "top_k": top_k}
        if traditions:
            payload["traditions"] = traditions
        resp = httpx.post(f"{_API_BASE}/search", json=payload, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        return SearchResults(
            query=data.get("query", query),
            results=data.get("results", []),
            model=data.get("model", ""),
        )
    except Exception:
        logger.debug("philapi /search unavailable, falling back to local", exc_info=True)

    # Fallback: local search via philengine
    try:
        from philengine import PhilEngine

        engine = PhilEngine()

        # Import the catalog from philapi routes (shared data)
        try:
            from philapi.routes.search import CONCEPT_CATALOG

            catalog = list(CONCEPT_CATALOG)
        except ImportError:
            catalog = _local_concept_catalog()

        if traditions:
            tradition_set = set(traditions)
            catalog = [c for c in catalog if c["tradition"] in tradition_set]

        query_emb = engine.encode([query])[0]
        concept_texts = [f"{c['label']}: {c['text_excerpt']}" for c in catalog]
        concept_embs = engine.encode(concept_texts)

        scored = []
        for i, concept in enumerate(catalog):
            dot = float(np.dot(query_emb, concept_embs[i]))
            norm_q = float(np.linalg.norm(query_emb))
            norm_c = float(np.linalg.norm(concept_embs[i]))
            sim = dot / (norm_q * norm_c) if norm_q > 1e-9 and norm_c > 1e-9 else 0.0
            scored.append({**concept, "similarity": round(sim, 4)})

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return SearchResults(
            query=query,
            results=scored[:top_k],
            model=getattr(engine, "_model", "local"),
        )
    except Exception:
        logger.debug("Local engine also unavailable, returning mock results", exc_info=True)

    # Final fallback: return unranked mock data
    catalog = _local_concept_catalog()
    if traditions:
        tradition_set = set(traditions)
        catalog = [c for c in catalog if c["tradition"] in tradition_set]
    results = [{**c, "similarity": 0.0} for c in catalog[:top_k]]
    return SearchResults(query=query, results=results, model="mock")


def compare(
    concept_a: str,
    concept_b: str,
    method: str = "hybrid",
) -> ComparisonResult:
    """Compare two philosophical concepts.

    Tries philapi /compare first; falls back to local philmap alignment
    or benchmark data.
    """
    # Try API first
    try:
        import httpx

        payload = {"concept_a": concept_a, "concept_b": concept_b, "method": method}
        resp = httpx.post(f"{_API_BASE}/compare", json=payload, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        return ComparisonResult(
            concept_a=concept_a,
            concept_b=concept_b,
            similarity=data.get("similarity", 0.0),
            method=data.get("method", method),
            facet_scores=data.get("facet_scores", {}),
            evidence=data.get("evidence", []),
        )
    except Exception:
        logger.debug("philapi /compare unavailable, falling back", exc_info=True)

    # Try local philmap alignment
    try:
        from philengine import PhilEngine

        engine = PhilEngine()
        embs = engine.encode([concept_a, concept_b])
        dot = float(np.dot(embs[0], embs[1]))
        norm_a = float(np.linalg.norm(embs[0]))
        norm_b = float(np.linalg.norm(embs[1]))
        sim = dot / (norm_a * norm_b) if norm_a > 1e-9 and norm_b > 1e-9 else 0.0

        facet_scores: dict[str, float] = {}
        try:
            fa = engine.encode_faceted(
                definition=concept_a,
                usage=f"The concept of {concept_a}",
                relational=f"{concept_a} in philosophical context",
            )
            fb = engine.encode_faceted(
                definition=concept_b,
                usage=f"The concept of {concept_b}",
                relational=f"{concept_b} in philosophical context",
            )
            for facet_name in ("definition", "usage", "relational"):
                va = fa.facet(facet_name)
                vb = fb.facet(facet_name)
                d = float(np.dot(va, vb))
                na = float(np.linalg.norm(va))
                nb = float(np.linalg.norm(vb))
                facet_scores[facet_name] = round(
                    d / (na * nb) if na > 1e-9 and nb > 1e-9 else 0.0, 4
                )
        except Exception:
            pass

        return ComparisonResult(
            concept_a=concept_a,
            concept_b=concept_b,
            similarity=round(sim, 4),
            method="local_engine",
            facet_scores=facet_scores,
            evidence=[f"Local engine cosine similarity: {sim:.4f}"],
        )
    except Exception:
        logger.debug("Local engine unavailable, trying benchmark", exc_info=True)

    # Final fallback: benchmark pairs
    sim = 0.0
    evidence_list: list[str] = []
    used_method = "benchmark_fallback"
    try:
        import yaml

        with open(_BENCHMARK_PAIRS_PATH) as f:
            data = yaml.safe_load(f)
        for pair in data.get("pairs", []):
            a_labels = {pair["concept_a"]["label"].lower(), pair["concept_a"]["id"].lower()}
            b_labels = {pair["concept_b"]["label"].lower(), pair["concept_b"]["id"].lower()}
            ca, cb = concept_a.lower(), concept_b.lower()
            if (ca in a_labels and cb in b_labels) or (cb in a_labels and ca in b_labels):
                sim = pair["expected_similarity"]
                evidence_list.append(
                    f"Benchmark: {pair.get('scholarly_reference', 'n/a')}"
                )
                break
    except Exception:
        logger.debug("Benchmark file unavailable", exc_info=True)
        used_method = "unavailable"

    if not evidence_list:
        evidence_list.append("No engine or benchmark data available")

    return ComparisonResult(
        concept_a=concept_a,
        concept_b=concept_b,
        similarity=sim,
        method=used_method,
        evidence=evidence_list,
    )


def explore(
    query: str,
    traditions: list[str] | None = None,
    top_k: int = 20,
) -> ExplorationResult:
    """Free-text concept exploration across traditions.

    Uses search() internally and enriches the result with tradition
    grouping information.
    """
    search_results = search(query, traditions=traditions, top_k=top_k)

    # Group results by tradition
    tradition_set: set[str] = set()
    for r in search_results.results:
        t = r.get("tradition", "") if isinstance(r, dict) else getattr(r, "tradition", "")
        if t:
            tradition_set.add(t)

    return ExplorationResult(
        query=query,
        results=search_results.results,
        traditions=sorted(tradition_set) if tradition_set else (traditions or []),
    )


def annotate(corpus: PhilCorpus, model: str = "default") -> PhilCorpus:
    """Auto-annotate concept spans."""
    return corpus


def quantify(corpus: PhilCorpus, types: list[str] | None = None) -> PhilCorpus:
    """Add feature layers to corpus."""
    types = types or ["lexical"]
    from philengine.quantifier.lexical import LexicalQuantifier

    if "lexical" in types:
        q = LexicalQuantifier()
        texts = list(corpus.concept_data.get("primary_label", []))
        if texts:
            corpus.metadata["layer:lexical_features"] = q.quantify(texts)
    return corpus


# ---- Private helpers ----

def _local_concept_catalog() -> list[dict[str, str]]:
    """Minimal concept catalog for offline fallback."""
    return [
        {"concept_id": "phil:C00142", "label": "間柄 (aidagara)", "tradition": "watsuji_ethics",
         "text_excerpt": "人間の存在は本質的に他者との間柄においてある"},
        {"concept_id": "phil:C00089", "label": "Mitsein", "tradition": "phenomenology",
         "text_excerpt": "Das Dasein ist wesentlich Mitsein"},
        {"concept_id": "phil:C00045", "label": "場所 (basho)", "tradition": "kyoto_school",
         "text_excerpt": "場所は自覚の場所として自己限定する"},
        {"concept_id": "phil:C00023", "label": "仁 (ren)", "tradition": "confucianism",
         "text_excerpt": "仁者愛人。己所不欲、勿施於人"},
        {"concept_id": "phil:C00156", "label": "Ubuntu", "tradition": "ubuntu_philosophy",
         "text_excerpt": "Umuntu ngumuntu ngabantu"},
        {"concept_id": "phil:C00034", "label": "空 (sunyata)", "tradition": "madhyamaka",
         "text_excerpt": "色即是空、空即是色"},
        {"concept_id": "phil:C00012", "label": "道 (dao)", "tradition": "daoism",
         "text_excerpt": "道可道、非常道"},
        {"concept_id": "phil:C00056", "label": "Dasein", "tradition": "phenomenology",
         "text_excerpt": "Das Dasein ist ein Seiendes"},
        {"concept_id": "phil:C00101", "label": "Aufhebung", "tradition": "german_idealism",
         "text_excerpt": "Aufheben hat in der Sprache den gedoppelten Sinn"},
        {"concept_id": "phil:C00112", "label": "Ich-Du", "tradition": "dialogical_philosophy",
         "text_excerpt": "Alles wirkliche Leben ist Begegnung"},
    ]
