"""ConceptSpans: positional concept annotations over text spans.

Maps concept occurrences to character or token ranges within texts,
analogous to GenomicRanges in Bioconductor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class ConceptSpans:
    """A set of concept annotation spans across philosophical texts.

    Each span records where a concept appears in a text, with start/end
    positions and optional scores.

    Parameters
    ----------
    spans : pd.DataFrame
        DataFrame with columns: text_id, concept_id, start, end.
        Optional columns: score, lang, method, annotator.
    metadata : dict
        Free-form metadata about how spans were generated.
    """

    spans: pd.DataFrame
    metadata: dict[str, object] = field(default_factory=dict)

    _REQUIRED_COLS: frozenset[str] = frozenset(
        {"text_id", "concept_id", "start", "end"}
    )

    def __post_init__(self) -> None:
        missing = self._REQUIRED_COLS - set(self.spans.columns)
        if missing:
            raise ValueError(f"spans DataFrame missing columns: {missing}")

    # ----- dimensions -----

    def __len__(self) -> int:
        return len(self.spans)

    @property
    def n_spans(self) -> int:
        return len(self.spans)

    @property
    def text_ids(self) -> list[str]:
        """Unique text IDs that contain at least one span."""
        return self.spans["text_id"].unique().tolist()

    @property
    def concept_ids(self) -> list[str]:
        """Unique concept IDs annotated across all spans."""
        return self.spans["concept_id"].unique().tolist()

    # ----- querying -----

    def by_text(self, text_id: str) -> ConceptSpans:
        """Return spans for a single text."""
        mask = self.spans["text_id"] == text_id
        return ConceptSpans(
            spans=self.spans.loc[mask].reset_index(drop=True),
            metadata=dict(self.metadata),
        )

    def by_concept(self, concept_id: str) -> ConceptSpans:
        """Return spans for a single concept."""
        mask = self.spans["concept_id"] == concept_id
        return ConceptSpans(
            spans=self.spans.loc[mask].reset_index(drop=True),
            metadata=dict(self.metadata),
        )

    def overlapping(self, text_id: str, start: int, end: int) -> ConceptSpans:
        """Return spans that overlap the given range within a text."""
        df = self.spans
        mask = (
            (df["text_id"] == text_id)
            & (df["start"] < end)
            & (df["end"] > start)
        )
        return ConceptSpans(
            spans=df.loc[mask].reset_index(drop=True),
            metadata=dict(self.metadata),
        )

    # ----- aggregation -----

    def to_count_matrix(self) -> tuple[np.ndarray, list[str], list[str]]:
        """Aggregate spans into a concept-by-text count matrix.

        Returns
        -------
        matrix : np.ndarray
            2-D array of shape (n_concepts, n_texts).
        concept_ids : list[str]
            Row labels.
        text_ids : list[str]
            Column labels.
        """
        pivot = self.spans.groupby(["concept_id", "text_id"]).size().unstack(
            fill_value=0
        )
        return (
            pivot.values,
            pivot.index.tolist(),
            pivot.columns.tolist(),
        )

    # ----- combination -----

    def append(self, other: ConceptSpans) -> ConceptSpans:
        """Concatenate two ConceptSpans objects."""
        combined = pd.concat(
            [self.spans, other.spans], ignore_index=True
        )
        return ConceptSpans(spans=combined, metadata=dict(self.metadata))

    # ----- representation -----

    def __repr__(self) -> str:
        return (
            f"ConceptSpans(n_spans={self.n_spans}, "
            f"n_texts={len(self.text_ids)}, "
            f"n_concepts={len(self.concept_ids)})"
        )
