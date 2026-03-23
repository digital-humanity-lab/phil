"""Unified verb API for Phil ecosystem."""
from __future__ import annotations
from typing import Any
from philcore.corpus import PhilCorpus
from .results import SearchResults, ComparisonResult, ExplorationResult

def read(source: str, section: str | None = None) -> PhilCorpus:
    """Read a philosophical text into a PhilCorpus."""
    return PhilCorpus(provenance={"source": source})

def embed(corpus: PhilCorpus, model: str = "default",
          layer_name: str = "embedding") -> PhilCorpus:
    """Embed all segments, add as new layer."""
    from philengine import PhilEngine
    engine = PhilEngine()
    texts = [s.get("text", "") for s in corpus.segment_data]
    if texts:
        embeddings = engine.encode(texts)
        corpus.add_layer(layer_name, embeddings)
    return corpus

def search(query: str, traditions: list[str] | None = None,
           top_k: int = 10) -> SearchResults:
    """Search for similar concepts/passages."""
    return SearchResults(query=query)

def compare(concept_a: str, concept_b: str,
            method: str = "hybrid") -> ComparisonResult:
    """Compare two philosophical concepts."""
    return ComparisonResult(concept_a=concept_a, concept_b=concept_b, method=method)

def explore(query: str, traditions: list[str] | None = None,
            top_k: int = 20) -> ExplorationResult:
    """Free-text concept exploration across traditions."""
    return ExplorationResult(query=query, traditions=traditions or [])

def annotate(corpus: PhilCorpus, model: str = "default") -> PhilCorpus:
    """Auto-annotate concept spans."""
    return corpus

def quantify(corpus: PhilCorpus, types: list[str] | None = None) -> PhilCorpus:
    """Add feature layers to corpus."""
    types = types or ["lexical"]
    from philengine.quantifier.lexical import LexicalQuantifier
    if "lexical" in types:
        q = LexicalQuantifier()
        texts = [s.get("text", "") for s in corpus.segment_data]
        if texts:
            corpus.add_layer("lexical_features", q.quantify(texts))
    return corpus
