"""Main corpus acquisition pipeline.

Example usage::

    from philcorpus import CorpusPipeline

    pipe = CorpusPipeline(
        sources=["gutenberg", "ctp", "aozora"],
        output_dir="./corpus_data",
    )

    # Fetch from all configured sources
    docs = pipe.fetch_all(limit_per_source=50)

    # Convert to PhilCorpus (segment-by-text matrix)
    corpus = pipe.to_philcorpus(docs)

    # Save for later use
    pipe.save(corpus, "./my_corpus.json")
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from philcorpus.registry import FetchRegistry
from philcorpus.sources.base import RawDocument

logger = logging.getLogger(__name__)

# Source name -> class import path
_SOURCE_REGISTRY: dict[str, str] = {
    "openalex": "philcorpus.sources.openalex.OpenAlexSource",
    "jstage": "philcorpus.sources.jstage.JStageSource",
    "philarchive": "philcorpus.sources.philarchive.PhilArchiveSource",
    "cinii": "philcorpus.sources.cinii.CiNiiSource",
    "gutenberg": "philcorpus.sources.gutenberg.GutenbergSource",
    "ctp": "philcorpus.sources.ctp.CTPSource",
    "aozora": "philcorpus.sources.aozora.AozoraSource",
}


def _import_source(dotpath: str) -> type:
    """Dynamically import a source class by dotted path."""
    module_path, class_name = dotpath.rsplit(".", 1)
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _segment_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraph-level segments."""
    if not text:
        return []
    # Split on double newlines or multiple newlines
    paragraphs = re.split(r"\n\s*\n", text)
    # Filter out very short segments (likely noise)
    return [p.strip() for p in paragraphs if len(p.strip()) > 20]


class CorpusPipeline:
    """Pipeline for fetching and assembling philosophical text corpora.

    Coordinates multiple data sources, tracks downloads via a registry,
    and converts raw documents into PhilCorpus format.

    Parameters
    ----------
    sources : list[str]
        Names of data sources to use (e.g., ["gutenberg", "ctp"]).
    output_dir : str or Path
        Directory for saving fetched data.

    Example
    -------
    >>> pipe = CorpusPipeline(["gutenberg", "ctp"], output_dir="./data")
    >>> docs = pipe.fetch_all(limit_per_source=10)
    >>> len(docs) > 0
    True
    """

    def __init__(
        self,
        sources: list[str],
        output_dir: str | Path = "./corpus_data",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.registry = FetchRegistry()
        self._sources: dict[str, dict[str, Any]] = {}

        for name in sources:
            self.add_source(name)

    def add_source(self, name: str, **kwargs: Any) -> None:
        """Add a data source to the pipeline.

        Parameters
        ----------
        name : str
            Source name (must be in the source registry).
        **kwargs
            Keyword arguments passed to the source constructor.
        """
        if name not in _SOURCE_REGISTRY:
            raise ValueError(
                f"Unknown source '{name}'. "
                f"Available: {list(_SOURCE_REGISTRY.keys())}"
            )
        self._sources[name] = kwargs

    def fetch_all(
        self,
        limit_per_source: int = 100,
        skip_fetched: bool = True,
    ) -> list[RawDocument]:
        """Fetch documents from all configured sources.

        Parameters
        ----------
        limit_per_source : int
            Maximum documents to fetch from each source.
        skip_fetched : bool
            If True, skip documents already in the registry.

        Returns
        -------
        list[RawDocument]
            All fetched documents.
        """
        all_docs: list[RawDocument] = []

        for name, kwargs in self._sources.items():
            logger.info("Fetching from %s...", name)
            try:
                source_cls = _import_source(_SOURCE_REGISTRY[name])
                source = source_cls(**kwargs)
                docs = source.fetch(limit=limit_per_source)

                if skip_fetched:
                    docs = [
                        d for d in docs if not self.registry.is_fetched(d.id)
                    ]

                # Mark as fetched
                for doc in docs:
                    self.registry.mark_fetched(doc.id, source=name)

                all_docs.extend(docs)
                logger.info("  Fetched %d documents from %s", len(docs), name)

            except Exception as e:
                logger.warning("Failed to fetch from %s: %s", name, e)

        return all_docs

    def to_philcorpus(self, documents: list[RawDocument]) -> Any:
        """Convert raw documents into a PhilCorpus object.

        Segments texts into paragraphs and builds the segment-by-text
        matrix with aligned metadata.

        Parameters
        ----------
        documents : list[RawDocument]
            Documents with fulltext populated.

        Returns
        -------
        PhilCorpus
            Corpus ready for embedding and analysis.
        """
        try:
            import numpy as np
            import pandas as pd
            from philcore import PhilCorpus
        except ImportError as e:
            raise ImportError(
                f"philcore, numpy, and pandas are required for "
                f"to_philcorpus: {e}"
            )

        # Build text metadata
        text_records: list[dict[str, Any]] = []
        all_segments: list[list[str]] = []

        for doc in documents:
            segments = _segment_into_paragraphs(doc.fulltext or doc.abstract or "")
            all_segments.append(segments)
            text_records.append({
                "doc_id": doc.id,
                "title": doc.title,
                "authors": ", ".join(doc.authors),
                "year": doc.year,
                "language": doc.language,
                "tradition": doc.tradition,
                "source": doc.source,
                "n_segments": len(segments),
            })

        text_data = pd.DataFrame(text_records)

        # Collect all unique segments
        segment_list: list[str] = []
        segment_doc_idx: list[int] = []
        for doc_idx, segments in enumerate(all_segments):
            for seg in segments:
                segment_list.append(seg)
                segment_doc_idx.append(doc_idx)

        segment_data = pd.DataFrame({
            "segment_text": segment_list,
            "doc_idx": segment_doc_idx,
            "char_count": [len(s) for s in segment_list],
        })

        # Create a segment-by-document occurrence matrix
        n_segments = len(segment_list)
        n_docs = len(documents)
        assay = np.zeros((n_segments, n_docs), dtype=np.float64)
        for seg_idx, doc_idx in enumerate(segment_doc_idx):
            assay[seg_idx, doc_idx] = 1.0

        return PhilCorpus(
            assay=assay,
            concept_data=segment_data,
            text_data=text_data,
            metadata={
                "name": "philcorpus_pipeline",
                "sources": list(self._sources.keys()),
                "n_documents": n_docs,
                "n_segments": n_segments,
            },
        )

    def save(self, corpus: Any, path: str | Path) -> None:
        """Save corpus metadata to JSON.

        Parameters
        ----------
        corpus : PhilCorpus
            The corpus to save.
        path : str or Path
            Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": corpus.metadata,
            "n_concepts": corpus.n_concepts,
            "n_texts": corpus.n_texts,
            "text_data": corpus.text_data.to_dict(orient="records"),
            "concept_data": corpus.concept_data.to_dict(orient="records"),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info("Saved corpus metadata to %s", path)
