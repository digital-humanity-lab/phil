"""Search endpoint."""
from __future__ import annotations

import logging

import numpy as np
from fastapi import APIRouter, Depends

from ..schemas import SearchRequest, SearchResponse, SearchResult
from ..dependencies import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()

# Hardcoded concept catalog for MVP (no vector DB yet)
CONCEPT_CATALOG: list[dict[str, str]] = [
    {
        "concept_id": "phil:C00142",
        "label": "間柄 (aidagara)",
        "tradition": "watsuji_ethics",
        "text_excerpt": "人間の存在は本質的に他者との間柄においてある",
    },
    {
        "concept_id": "phil:C00089",
        "label": "Mitsein",
        "tradition": "phenomenology",
        "text_excerpt": "Das Dasein ist wesentlich Mitsein",
    },
    {
        "concept_id": "phil:C00045",
        "label": "場所 (basho)",
        "tradition": "kyoto_school",
        "text_excerpt": "場所は自覚の場所として自己限定する",
    },
    {
        "concept_id": "phil:C00091",
        "label": "Lichtung",
        "tradition": "phenomenology",
        "text_excerpt": "Die Lichtung ist der Ort des Seinsgeschehens",
    },
    {
        "concept_id": "phil:C00023",
        "label": "仁 (ren)",
        "tradition": "confucianism",
        "text_excerpt": "仁者愛人。己所不欲、勿施於人",
    },
    {
        "concept_id": "phil:C00156",
        "label": "Ubuntu",
        "tradition": "ubuntu_philosophy",
        "text_excerpt": "Umuntu ngumuntu ngabantu — a person is a person through other persons",
    },
    {
        "concept_id": "phil:C00034",
        "label": "空 (sunyata)",
        "tradition": "madhyamaka",
        "text_excerpt": "色即是空、空即是色。一切法空",
    },
    {
        "concept_id": "phil:C00167",
        "label": "Différance",
        "tradition": "poststructuralism",
        "text_excerpt": "La différance est le jeu systématique des différences",
    },
    {
        "concept_id": "phil:C00012",
        "label": "道 (dao)",
        "tradition": "daoism",
        "text_excerpt": "道可道、非常道。名可名、非常名",
    },
    {
        "concept_id": "phil:C00178",
        "label": "Logos",
        "tradition": "ancient_greek",
        "text_excerpt": "ἐν ἀρχῇ ἦν ὁ λόγος — the rational principle governing the cosmos",
    },
    {
        "concept_id": "phil:C00001",
        "label": "autonomy",
        "tradition": "kantian_ethics",
        "text_excerpt": "Autonomie des Willens ist die Beschaffenheit des Willens",
    },
    {
        "concept_id": "phil:C00056",
        "label": "Dasein",
        "tradition": "phenomenology",
        "text_excerpt": "Das Dasein ist ein Seiendes, dem es in seinem Sein um dieses Sein selbst geht",
    },
    {
        "concept_id": "phil:C00078",
        "label": "karma",
        "tradition": "hinduism",
        "text_excerpt": "karmaṇy evādhikāras te mā phaleṣu kadācana",
    },
    {
        "concept_id": "phil:C00101",
        "label": "Aufhebung",
        "tradition": "german_idealism",
        "text_excerpt": "Aufheben hat in der Sprache den gedoppelten Sinn",
    },
    {
        "concept_id": "phil:C00112",
        "label": "Ich-Du",
        "tradition": "dialogical_philosophy",
        "text_excerpt": "Alles wirkliche Leben ist Begegnung",
    },
    {
        "concept_id": "phil:C00123",
        "label": "li (理)",
        "tradition": "neo_confucianism",
        "text_excerpt": "理は天地万物の根本原理である",
    },
    {
        "concept_id": "phil:C00145",
        "label": "pratityasamutpada",
        "tradition": "buddhism",
        "text_excerpt": "imasmiṃ sati idaṃ hoti — when this exists, that comes to be",
    },
    {
        "concept_id": "phil:C00090",
        "label": "atman",
        "tradition": "vedanta",
        "text_excerpt": "tat tvam asi — thou art that; the self is Brahman",
    },
    {
        "concept_id": "phil:C00134",
        "label": "Eidos",
        "tradition": "platonism",
        "text_excerpt": "τὸ εἶδος — the unchanging form apprehended by the intellect",
    },
    {
        "concept_id": "phil:C00189",
        "label": "Gelassenheit",
        "tradition": "phenomenology",
        "text_excerpt": "Gelassenheit zu den Dingen und die Offenheit für das Geheimnis",
    },
]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return dot / (norm_a * norm_b)


@router.post("/search", response_model=SearchResponse)
async def search_concepts(req: SearchRequest, engine=Depends(get_engine)):
    """Search for philosophical concepts similar to a query string."""
    catalog = CONCEPT_CATALOG

    # Filter by tradition if specified
    if req.traditions:
        tradition_set = set(req.traditions)
        catalog = [c for c in catalog if c["tradition"] in tradition_set]

    model_name = "default"

    # Try to use the engine for semantic ranking
    try:
        query_emb = engine.encode([req.query])[0]
        model_name = getattr(engine, "_model", "default")

        concept_texts = [
            f"{c['label']}: {c['text_excerpt']}" for c in catalog
        ]
        concept_embs = engine.encode(concept_texts)

        scored = []
        for i, concept in enumerate(catalog):
            sim = _cosine_similarity(query_emb, concept_embs[i])
            scored.append((concept, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        scored = scored[: req.top_k]

        results = [
            SearchResult(
                concept_id=c["concept_id"],
                label=c["label"],
                similarity=round(sim, 4),
                tradition=c["tradition"],
                text_excerpt=c["text_excerpt"],
            )
            for c, sim in scored
        ]
    except Exception:
        logger.warning(
            "Engine unavailable for search, returning unranked results",
            exc_info=True,
        )
        # Fallback: return all matching concepts with similarity=0
        results = [
            SearchResult(
                concept_id=c["concept_id"],
                label=c["label"],
                similarity=0.0,
                tradition=c["tradition"],
                text_excerpt=c["text_excerpt"],
            )
            for c in catalog[: req.top_k]
        ]

    return SearchResponse(results=results, query=req.query, model=model_name)
