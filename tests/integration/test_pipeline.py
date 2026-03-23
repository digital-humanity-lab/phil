"""Integration tests: end-to-end pipeline with PhilCorpus and ConceptSpans."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from philcore.models.concept import Concept, ConceptLabel
from philcore.models.text import Text
from philcore.corpus import PhilCorpus
from philcore.collection import PhilCollection
from philcore.spans import ConceptSpans


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_concepts() -> list[Concept]:
    """Three sample concepts from different traditions."""
    return [
        Concept(
            id="ren",
            labels=[ConceptLabel(text="仁", lang="zho", is_primary=True),
                    ConceptLabel(text="ren", lang="eng")],
            tradition_ids=["confucianism"],
            definition="Benevolence / humaneness in Confucian ethics.",
        ),
        Concept(
            id="dasein",
            labels=[ConceptLabel(text="Dasein", lang="deu", is_primary=True),
                    ConceptLabel(text="being-there", lang="eng")],
            tradition_ids=["phenomenology"],
            definition="Heidegger's term for the being that questions its own being.",
        ),
        Concept(
            id="ubuntu",
            labels=[ConceptLabel(text="ubuntu", lang="zul", is_primary=True)],
            tradition_ids=["african"],
            definition="I am because we are.",
        ),
    ]


@pytest.fixture()
def sample_texts() -> list[Text]:
    """Two sample texts."""
    return [
        Text(
            id="analects",
            labels=[ConceptLabel(text="論語", lang="zho", is_primary=True)],
            lang="zho",
            tradition_ids=["confucianism"],
        ),
        Text(
            id="sein_und_zeit",
            labels=[ConceptLabel(text="Sein und Zeit", lang="deu", is_primary=True)],
            lang="deu",
            tradition_ids=["phenomenology"],
        ),
    ]


# ---------------------------------------------------------------------------
# 1. PhilCorpus creation from model objects
# ---------------------------------------------------------------------------

class TestPhilCorpus:
    def test_create_from_concepts_and_texts(
        self, sample_concepts: list[Concept], sample_texts: list[Text]
    ) -> None:
        corpus = PhilCorpus.from_concepts_and_texts(sample_concepts, sample_texts)

        assert corpus.n_concepts == 3
        assert corpus.n_texts == 2
        assert corpus.shape == (3, 2)
        assert corpus.assay.dtype == np.float64

    def test_create_with_custom_assay(
        self, sample_concepts: list[Concept], sample_texts: list[Text]
    ) -> None:
        assay = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]])
        corpus = PhilCorpus.from_concepts_and_texts(
            sample_concepts, sample_texts, assay=assay
        )
        np.testing.assert_array_equal(corpus.assay, assay)

    def test_dimension_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="concept_data"):
            PhilCorpus(
                assay=np.zeros((2, 3)),
                concept_data=pd.DataFrame({"a": [1]}),  # 1 row != 2
                text_data=pd.DataFrame({"b": [1, 2, 3]}),
            )

    def test_subset_concepts(
        self, sample_concepts: list[Concept], sample_texts: list[Text]
    ) -> None:
        corpus = PhilCorpus.from_concepts_and_texts(sample_concepts, sample_texts)
        sub = corpus.subset_concepts([0, 2])

        assert sub.n_concepts == 2
        assert sub.n_texts == 2

    def test_subset_texts(
        self, sample_concepts: list[Concept], sample_texts: list[Text]
    ) -> None:
        corpus = PhilCorpus.from_concepts_and_texts(sample_concepts, sample_texts)
        sub = corpus.subset_texts([1])

        assert sub.n_concepts == 3
        assert sub.n_texts == 1


# ---------------------------------------------------------------------------
# 2. PhilCollection – adding layers
# ---------------------------------------------------------------------------

class TestPhilCollection:
    def test_add_layers(
        self, sample_concepts: list[Concept], sample_texts: list[Text]
    ) -> None:
        corpus_counts = PhilCorpus.from_concepts_and_texts(
            sample_concepts, sample_texts,
            assay=np.array([[3, 0], [0, 5], [1, 1]], dtype=np.float64),
        )
        corpus_tfidf = PhilCorpus.from_concepts_and_texts(
            sample_concepts, sample_texts,
            assay=np.array([[0.6, 0.0], [0.0, 0.8], [0.2, 0.2]]),
        )

        coll = PhilCollection()
        coll.add_corpus("counts", corpus_counts)
        coll.add_corpus("tfidf", corpus_tfidf)

        assert len(coll) == 2
        assert coll.assay_names == ["counts", "tfidf"]
        assert coll.n_texts == 2
        np.testing.assert_array_equal(coll["counts"].assay[0, 0], 3)

    def test_subset_collection(
        self, sample_concepts: list[Concept], sample_texts: list[Text]
    ) -> None:
        corpus = PhilCorpus.from_concepts_and_texts(sample_concepts, sample_texts)
        coll = PhilCollection()
        coll.add_corpus("main", corpus)

        sub = coll.subset_texts([0])
        assert sub.n_texts == 1
        assert sub["main"].n_texts == 1


# ---------------------------------------------------------------------------
# 3. ConceptSpans creation and filtering
# ---------------------------------------------------------------------------

class TestConceptSpans:
    @pytest.fixture()
    def spans(self) -> ConceptSpans:
        df = pd.DataFrame([
            {"text_id": "analects", "concept_id": "phil:C001", "start": 0, "end": 10,
             "confidence": 0.95},
            {"text_id": "analects", "concept_id": "phil:C002", "start": 15, "end": 25,
             "confidence": 0.80},
            {"text_id": "sein_und_zeit", "concept_id": "phil:C001", "start": 100, "end": 150,
             "confidence": 0.90},
            {"text_id": "sein_und_zeit", "concept_id": "phil:C003", "start": 200, "end": 250,
             "confidence": 0.70},
        ])
        return ConceptSpans(spans=df, metadata={"annotator": "test"})

    def test_creation(self, spans: ConceptSpans) -> None:
        assert len(spans) == 4
        assert spans.n_spans == 4

    def test_missing_columns_raises(self) -> None:
        with pytest.raises(ValueError, match="missing columns"):
            ConceptSpans(spans=pd.DataFrame({"text_id": ["a"], "start": [0]}))

    def test_filter_by_text(self, spans: ConceptSpans) -> None:
        analects_spans = spans.by_text("analects")
        assert analects_spans.n_spans == 2
        assert all(tid == "analects" for tid in analects_spans.spans["text_id"])

    def test_filter_by_concept(self, spans: ConceptSpans) -> None:
        c001 = spans.by_concept("phil:C001")
        assert c001.n_spans == 2
        assert set(c001.text_ids) == {"analects", "sein_und_zeit"}

    def test_overlapping(self, spans: ConceptSpans) -> None:
        overlap = spans.overlapping("analects", 5, 20)
        assert overlap.n_spans == 2  # both analects spans overlap [5, 20)

    def test_unique_ids(self, spans: ConceptSpans) -> None:
        assert set(spans.text_ids) == {"analects", "sein_und_zeit"}
        assert set(spans.concept_ids) == {"phil:C001", "phil:C002", "phil:C003"}

    def test_count_matrix(self, spans: ConceptSpans) -> None:
        matrix, concept_ids, text_ids = spans.to_count_matrix()
        assert matrix.shape[0] == len(concept_ids)
        assert matrix.shape[1] == len(text_ids)
        assert matrix.sum() == 4

    def test_append(self, spans: ConceptSpans) -> None:
        extra = ConceptSpans(
            spans=pd.DataFrame([
                {"text_id": "republic", "concept_id": "phil:C010",
                 "start": 0, "end": 50},
            ])
        )
        combined = spans.append(extra)
        assert combined.n_spans == 5
