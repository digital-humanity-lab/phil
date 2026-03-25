"""Method-chaining pipeline for Phil ecosystem."""
from __future__ import annotations
from typing import Any
from philcore.corpus import PhilCorpus
from . import verbs
from .results import SearchResults, ComparisonResult, ExplorationResult

class PhilPipeline:
    def __init__(self, source: str | PhilCorpus | None = None):
        if isinstance(source, str):
            self._corpus = verbs.read(source)
        elif isinstance(source, PhilCorpus):
            self._corpus = source
        else:
            self._corpus = PhilCorpus()
        self._result: Any = None

    def embed(self, model: str = "default", layer_name: str = "embedding") -> PhilPipeline:
        self._corpus = verbs.embed(self._corpus, model=model, layer_name=layer_name)
        return self

    def search(self, concept: str | None = None, traditions: list[str] | None = None,
               top_k: int = 10) -> PhilPipeline:
        self._result = verbs.search(concept or "", traditions=traditions, top_k=top_k)
        return self

    def compare(self, concept_a: str, concept_b: str,
                method: str = "hybrid") -> PhilPipeline:
        self._result = verbs.compare(concept_a, concept_b, method=method)
        return self

    def quantify(self, types: list[str] | None = None) -> PhilPipeline:
        self._corpus = verbs.quantify(self._corpus, types=types)
        return self

    @property
    def result(self) -> Any:
        return self._result or self._corpus

    def __repr__(self) -> str:
        return repr(self.result)
