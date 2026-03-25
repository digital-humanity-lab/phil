"""Interpretation tracking and term evolution analysis.

Combines interpretation tracking (making interpretive pluralism explicit)
with term semantic evolution tracking.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import numpy as np

from philengine import PhilEngine


@dataclass
class Interpretation:
    """A scholarly interpretation of a text passage or concept."""
    id: str
    interpreter: str
    target_text: str
    target_ref: str
    reading: str
    evidence: list[str] = field(default_factory=list)
    school_of_interpretation: str = ""
    published_in: str = ""
    date: Optional[date] = None
    tags: list[str] = field(default_factory=list)

    def conflicts_with(self, other: Interpretation) -> bool:
        return (self.target_ref == other.target_ref
                and self.reading != other.reading)


class InterpretationTracker:
    """Track and compare scholarly interpretations.

    Design principle: philosophy depends on texts, but interpretation
    is inherently perspectival. This class makes interpretive differences
    explicit.
    """

    def __init__(self) -> None:
        self._by_ref: dict[str, list[Interpretation]] = defaultdict(list)
        self._by_interpreter: dict[str, list[Interpretation]] = defaultdict(list)
        self._all: list[Interpretation] = []

    def add(self, interpretation: Interpretation) -> None:
        self._all.append(interpretation)
        self._by_ref[interpretation.target_ref].append(interpretation)
        self._by_interpreter[interpretation.interpreter].append(interpretation)

    def add_batch(self, interpretations: list[Interpretation]) -> None:
        for interp in interpretations:
            self.add(interp)

    def find_conflicts(
        self, target_ref: str
    ) -> list[tuple[Interpretation, Interpretation]]:
        interps = self._by_ref.get(target_ref, [])
        conflicts = []
        for i, a in enumerate(interps):
            for b in interps[i + 1:]:
                if a.conflicts_with(b):
                    conflicts.append((a, b))
        return conflicts

    def get_by_school(self, school: str) -> list[Interpretation]:
        return [i for i in self._all if i.school_of_interpretation == school]

    def interpreters_for(self, target_ref: str) -> list[str]:
        return list({i.interpreter for i in self._by_ref.get(target_ref, [])})

    def summarize_debate(self, target_ref: str) -> dict:
        interps = self._by_ref.get(target_ref, [])
        if not interps:
            return {"target_ref": target_ref, "status": "no_interpretations_found"}

        by_school: dict[str, list[Interpretation]] = defaultdict(list)
        for interp in interps:
            by_school[interp.school_of_interpretation or "unspecified"].append(interp)

        conflicts = self.find_conflicts(target_ref)
        return {
            "target_ref": target_ref,
            "target_text": interps[0].target_text,
            "num_interpretations": len(interps),
            "interpreters": [i.interpreter for i in interps],
            "schools_represented": list(by_school.keys()),
            "readings_by_school": {
                school: [i.reading for i in group]
                for school, group in by_school.items()
            },
            "num_conflicts": len(conflicts),
            "conflict_pairs": [
                {"a": a.interpreter, "b": b.interpreter,
                 "a_reading": a.reading, "b_reading": b.reading}
                for a, b in conflicts
            ],
        }


@dataclass
class TermUsage:
    term: str
    context: str
    source_id: str
    author: str
    date: Optional[str] = None
    definition_given: str = ""


class TermEvolution:
    """Track how a philosophical term's meaning evolves over time."""

    def __init__(self, engine: PhilEngine | None = None):
        self._engine = engine
        self._usages: list[TermUsage] = []

    def _get_engine(self) -> PhilEngine:
        if self._engine is None:
            self._engine = PhilEngine()
        return self._engine

    def add_usage(self, usage: TermUsage) -> None:
        self._usages.append(usage)

    def add_usages(self, usages: list[TermUsage]) -> None:
        self._usages.extend(usages)

    def trace(self, term: str) -> dict:
        relevant = [u for u in self._usages if u.term.lower() == term.lower()]
        relevant.sort(key=lambda u: u.date or "")

        if len(relevant) < 2:
            return {"term": term, "usages": len(relevant),
                    "evolution": "insufficient_data"}

        engine = self._get_engine()
        contexts = [u.context for u in relevant]
        embeddings = engine.encode(contexts)

        shifts = []
        for i in range(len(embeddings) - 1):
            sim = float(
                np.dot(embeddings[i], embeddings[i + 1])
                / (np.linalg.norm(embeddings[i])
                   * np.linalg.norm(embeddings[i + 1]) + 1e-9)
            )
            shifts.append({
                "from": {"source": relevant[i].source_id,
                         "date": relevant[i].date,
                         "context": relevant[i].context[:200]},
                "to": {"source": relevant[i + 1].source_id,
                       "date": relevant[i + 1].date,
                       "context": relevant[i + 1].context[:200]},
                "semantic_similarity": sim,
                "shift_detected": sim < 0.70,
            })

        meaning_clusters: dict[int, list[dict]] = {}
        try:
            from sklearn.cluster import AgglomerativeClustering
            if len(embeddings) >= 3:
                clustering = AgglomerativeClustering(
                    n_clusters=None, distance_threshold=0.5,
                    metric="cosine", linkage="average",
                )
                labels = clustering.fit_predict(embeddings)
                for label, usage in zip(labels, relevant):
                    meaning_clusters.setdefault(int(label), []).append(
                        {"source": usage.source_id, "date": usage.date}
                    )
            else:
                meaning_clusters = {0: [{"source": u.source_id, "date": u.date}
                                        for u in relevant]}
        except ImportError:
            meaning_clusters = {0: [{"source": u.source_id, "date": u.date}
                                    for u in relevant]}

        return {
            "term": term,
            "num_usages": len(relevant),
            "date_range": (relevant[0].date, relevant[-1].date),
            "chronological_shifts": shifts,
            "meaning_clusters": meaning_clusters,
            "num_distinct_meanings": len(meaning_clusters),
        }
