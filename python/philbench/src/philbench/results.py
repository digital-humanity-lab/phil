"""Result types for philbench operations."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class SearchResults:
    query: str
    results: list[dict] = field(default_factory=list)
    model: str = ""
    def __repr__(self):
        lines = [f'SearchResults: "{self.query}" ({len(self.results)} results)']
        for i, r in enumerate(self.results[:5]):
            lines.append(f"  {i+1}. {r.get('label', '?')} ({r.get('similarity', 0):.3f}) [{r.get('tradition', '')}]")
        if len(self.results) > 5:
            lines.append(f"  ... and {len(self.results)-5} more")
        return "\n".join(lines)

@dataclass
class ComparisonResult:
    concept_a: str
    concept_b: str
    similarity: float = 0.0
    method: str = "hybrid"
    facet_scores: dict[str, float] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    def __repr__(self):
        lines = [f"Comparison: {self.concept_a} <-> {self.concept_b}",
                 f"  Similarity: {self.similarity:.3f} ({self.method})"]
        for k, v in self.facet_scores.items():
            lines.append(f"  {k}: {v:.3f}")
        return "\n".join(lines)

@dataclass
class ExplorationResult:
    query: str
    results: list[dict] = field(default_factory=list)
    traditions: list[str] = field(default_factory=list)
    def __repr__(self):
        lines = [f'Exploration: "{self.query}"',
                 f"  {len(self.results)} concepts across {len(self.traditions)} traditions"]
        return "\n".join(lines)
