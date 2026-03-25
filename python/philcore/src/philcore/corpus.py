"""PhilCorpus: SummarizedExperiment-style container for philosophical text corpora.

Stores a concept-by-text matrix alongside row (concept) and column (text)
metadata, analogous to SummarizedExperiment in Bioconductor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from philcore.models.concept import Concept
from philcore.models.text import Text


@dataclass
class PhilCorpus:
    """A concept-by-text matrix with aligned metadata.

    Parameters
    ----------
    assay : np.ndarray
        2-D numeric matrix of shape (n_concepts, n_texts). Values may
        represent concept occurrence counts, TF-IDF weights, or embedding
        similarity scores.
    concept_data : pd.DataFrame
        Row metadata with one row per concept. Index must match the row
        order of *assay*.
    text_data : pd.DataFrame
        Column metadata with one row per text. Index must match the
        column order of *assay*.
    metadata : dict
        Free-form corpus-level metadata (name, version, provenance, etc.).
    """

    assay: np.ndarray
    concept_data: pd.DataFrame
    text_data: pd.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n_rows, n_cols = self.assay.shape
        if len(self.concept_data) != n_rows:
            raise ValueError(
                f"concept_data has {len(self.concept_data)} rows but assay "
                f"has {n_rows} rows"
            )
        if len(self.text_data) != n_cols:
            raise ValueError(
                f"text_data has {len(self.text_data)} rows but assay "
                f"has {n_cols} columns"
            )

    # ----- dimensions -----

    @property
    def n_concepts(self) -> int:
        return self.assay.shape[0]

    @property
    def n_texts(self) -> int:
        return self.assay.shape[1]

    @property
    def shape(self) -> tuple[int, int]:
        return self.assay.shape  # type: ignore[return-value]

    # ----- subsetting -----

    def subset_concepts(self, idx: list[int] | np.ndarray) -> PhilCorpus:
        """Return a new PhilCorpus with a subset of concepts (rows)."""
        return PhilCorpus(
            assay=self.assay[idx, :],
            concept_data=self.concept_data.iloc[idx].reset_index(drop=True),
            text_data=self.text_data.copy(),
            metadata=dict(self.metadata),
        )

    def subset_texts(self, idx: list[int] | np.ndarray) -> PhilCorpus:
        """Return a new PhilCorpus with a subset of texts (columns)."""
        return PhilCorpus(
            assay=self.assay[:, idx],
            concept_data=self.concept_data.copy(),
            text_data=self.text_data.iloc[idx].reset_index(drop=True),
            metadata=dict(self.metadata),
        )

    # ----- convenience constructors -----

    @classmethod
    def from_concepts_and_texts(
        cls,
        concepts: list[Concept],
        texts: list[Text],
        assay: np.ndarray | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PhilCorpus:
        """Build a PhilCorpus from lists of Concept and Text objects.

        If *assay* is ``None`` a zero matrix is created.
        """
        concept_records = [
            {
                "concept_id": c.id,
                "primary_label": c.primary_label.text,
                "tradition_ids": c.tradition_ids,
            }
            for c in concepts
        ]
        text_records = [
            {
                "text_id": t.id,
                "primary_label": t.labels[0].text,
                "lang": t.lang,
            }
            for t in texts
        ]
        if assay is None:
            assay = np.zeros((len(concepts), len(texts)), dtype=np.float64)

        return cls(
            assay=assay,
            concept_data=pd.DataFrame(concept_records),
            text_data=pd.DataFrame(text_records),
            metadata=metadata or {},
        )

    # ----- representation -----

    def __repr__(self) -> str:
        return (
            f"PhilCorpus(n_concepts={self.n_concepts}, "
            f"n_texts={self.n_texts})"
        )
