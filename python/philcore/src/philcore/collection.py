"""PhilCollection: multi-assay container for philosophical data.

Bundles multiple PhilCorpus assays (e.g. occurrence counts, TF-IDF,
embeddings) that share the same set of texts, analogous to
MultiAssayExperiment in Bioconductor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from philcore.corpus import PhilCorpus


@dataclass
class PhilCollection:
    """A named collection of PhilCorpus objects sharing column (text) metadata.

    Parameters
    ----------
    corpora : dict[str, PhilCorpus]
        Named assay layers.  Keys are assay names (e.g. ``"counts"``,
        ``"tfidf"``, ``"embedding"``).
    text_data : pd.DataFrame
        Shared column metadata across all corpora.
    metadata : dict
        Collection-level metadata (name, version, provenance, etc.).
    """

    corpora: dict[str, PhilCorpus] = field(default_factory=dict)
    text_data: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.text_data) > 0:
            for name, corpus in self.corpora.items():
                if corpus.n_texts != len(self.text_data):
                    raise ValueError(
                        f"Corpus '{name}' has {corpus.n_texts} texts "
                        f"but text_data has {len(self.text_data)} rows"
                    )

    # ----- accessors -----

    @property
    def assay_names(self) -> list[str]:
        return list(self.corpora.keys())

    @property
    def n_texts(self) -> int:
        return len(self.text_data)

    def __getitem__(self, name: str) -> PhilCorpus:
        return self.corpora[name]

    def __contains__(self, name: str) -> bool:
        return name in self.corpora

    def __len__(self) -> int:
        return len(self.corpora)

    # ----- mutation -----

    def add_corpus(self, name: str, corpus: PhilCorpus) -> None:
        """Add a named PhilCorpus layer.

        Validates that its text dimension matches the collection's
        shared text_data.
        """
        if len(self.text_data) > 0 and corpus.n_texts != len(self.text_data):
            raise ValueError(
                f"Corpus '{name}' has {corpus.n_texts} texts but collection "
                f"has {len(self.text_data)}"
            )
        if len(self.text_data) == 0 and len(self.corpora) == 0:
            self.text_data = corpus.text_data.copy()
        self.corpora[name] = corpus

    def remove_corpus(self, name: str) -> PhilCorpus:
        """Remove and return a named corpus layer."""
        return self.corpora.pop(name)

    # ----- subsetting -----

    def subset_texts(self, idx: list[int]) -> PhilCollection:
        """Return a new PhilCollection with a subset of texts."""
        new_corpora = {
            name: corpus.subset_texts(idx)
            for name, corpus in self.corpora.items()
        }
        return PhilCollection(
            corpora=new_corpora,
            text_data=self.text_data.iloc[idx].reset_index(drop=True),
            metadata=dict(self.metadata),
        )

    # ----- summary -----

    def summary(self) -> pd.DataFrame:
        """Return a summary DataFrame with one row per corpus layer."""
        rows = []
        for name, corpus in self.corpora.items():
            rows.append({
                "assay": name,
                "n_concepts": corpus.n_concepts,
                "n_texts": corpus.n_texts,
                "dtype": str(corpus.assay.dtype),
            })
        return pd.DataFrame(rows)

    # ----- representation -----

    def __repr__(self) -> str:
        assays = ", ".join(self.assay_names) if self.assay_names else "none"
        return (
            f"PhilCollection(n_texts={self.n_texts}, "
            f"assays=[{assays}])"
        )
