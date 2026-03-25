"""Tests for philcorpus data sources and pipeline."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from philcorpus.sources.base import DataSource, RawDocument
from philcorpus.sources.openalex import OpenAlexSource
from philcorpus.sources.jstage import JStageSource
from philcorpus.sources.gutenberg import GutenbergSource
from philcorpus.sources.ctp import CTPSource
from philcorpus.sources.aozora import AozoraSource
from philcorpus.sources.philarchive import PhilArchiveSource
from philcorpus.sources.cinii import CiNiiSource
from philcorpus.pipeline import CorpusPipeline
from philcorpus.registry import FetchRegistry


class TestRawDocument:
    """Tests for the RawDocument dataclass."""

    def test_raw_document_creation(self) -> None:
        doc = RawDocument(
            id="test:001",
            title="On the Nature of Being",
            authors=["Aristotle"],
            year=-350,
            language="grc",
            tradition="greek",
            source="gutenberg",
            url="https://example.com/test",
        )
        assert doc.id == "test:001"
        assert doc.title == "On the Nature of Being"
        assert doc.authors == ["Aristotle"]
        assert doc.year == -350
        assert doc.language == "grc"
        assert doc.tradition == "greek"
        assert doc.source == "gutenberg"
        assert doc.fulltext is None
        assert doc.abstract is None
        assert doc.metadata == {}

    def test_raw_document_with_optional_fields(self) -> None:
        doc = RawDocument(
            id="test:002",
            title="Test Paper",
            authors=["Author A", "Author B"],
            year=2024,
            language="en",
            tradition="western",
            source="openalex",
            url="https://doi.org/10.1234/test",
            fulltext_url="https://example.com/pdf",
            license="cc-by-4.0",
            abstract="This is a test abstract.",
            fulltext="Full text content here.",
            metadata={"cited_by_count": 42},
        )
        assert doc.fulltext_url == "https://example.com/pdf"
        assert doc.license == "cc-by-4.0"
        assert doc.abstract == "This is a test abstract."
        assert doc.fulltext == "Full text content here."
        assert doc.metadata["cited_by_count"] == 42


class TestSourceInstantiation:
    """Test that all source classes can be instantiated without API calls."""

    def test_openalex_source_init(self) -> None:
        source = OpenAlexSource()
        assert source.email == "digital-philosophy@example.com"

    def test_openalex_source_custom_email(self) -> None:
        source = OpenAlexSource(email="test@example.com")
        assert source.email == "test@example.com"

    def test_jstage_source_init(self) -> None:
        source = JStageSource()
        assert len(source.journals) > 0
        assert "哲学研究" in source.journals

    def test_jstage_source_custom_journals(self) -> None:
        source = JStageSource(journals=["哲学研究"])
        assert source.journals == ["哲学研究"]

    def test_gutenberg_source_init(self) -> None:
        source = GutenbergSource()
        assert len(source.works) > 0

    def test_ctp_source_init(self) -> None:
        source = CTPSource()
        assert "confucianism" in source.traditions
        assert "daoism" in source.traditions

    def test_ctp_source_custom_traditions(self) -> None:
        source = CTPSource(traditions=["daoism"])
        assert source.traditions == ["daoism"]

    def test_aozora_source_init(self) -> None:
        source = AozoraSource()
        assert "西田幾多郎" in source.authors

    def test_philarchive_source_init(self) -> None:
        source = PhilArchiveSource()
        assert isinstance(source, PhilArchiveSource)

    def test_cinii_source_init(self) -> None:
        source = CiNiiSource()
        assert isinstance(source, CiNiiSource)

    def test_sources_implement_protocol(self) -> None:
        """All sources should have a fetch method compatible with DataSource."""
        sources = [
            OpenAlexSource(),
            JStageSource(),
            GutenbergSource(),
            CTPSource(),
            AozoraSource(),
            PhilArchiveSource(),
            CiNiiSource(),
        ]
        for source in sources:
            assert hasattr(source, "fetch")
            assert callable(source.fetch)


class TestGutenbergSourceLocal:
    """Test GutenbergSource without network calls."""

    def test_fetch_filters_by_query(self) -> None:
        source = GutenbergSource()
        docs = source.fetch(query="plato", download_fulltext=False)
        assert all("Plato" in d.authors[0] for d in docs)

    def test_fetch_respects_limit(self) -> None:
        source = GutenbergSource()
        docs = source.fetch(limit=3, download_fulltext=False)
        assert len(docs) <= 3

    def test_fetch_returns_raw_documents(self) -> None:
        source = GutenbergSource()
        docs = source.fetch(limit=1, download_fulltext=False)
        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc, RawDocument)
        assert doc.source == "gutenberg"
        assert doc.license == "public_domain"


class TestCTPSourceLocal:
    """Test CTPSource without network calls."""

    def test_fetch_all_traditions(self) -> None:
        source = CTPSource()
        docs = source.fetch(download_fulltext=False)
        traditions = {d.tradition for d in docs}
        assert "confucianism" in traditions
        assert "daoism" in traditions

    def test_fetch_single_tradition(self) -> None:
        source = CTPSource(traditions=["daoism"])
        docs = source.fetch(download_fulltext=False)
        assert all(d.tradition == "daoism" for d in docs)

    def test_fetch_with_query(self) -> None:
        source = CTPSource()
        docs = source.fetch(query="Dao De Jing", download_fulltext=False)
        assert any("道徳経" in d.title for d in docs)


class TestPipelineCreation:
    """Test CorpusPipeline initialization."""

    def test_pipeline_creation(self) -> None:
        pipe = CorpusPipeline(
            sources=["gutenberg", "ctp"],
            output_dir="/tmp/test_corpus",
        )
        assert "gutenberg" in pipe._sources
        assert "ctp" in pipe._sources

    def test_pipeline_invalid_source(self) -> None:
        with pytest.raises(ValueError, match="Unknown source"):
            CorpusPipeline(sources=["nonexistent"])

    def test_pipeline_add_source(self) -> None:
        pipe = CorpusPipeline(sources=["gutenberg"])
        pipe.add_source("ctp")
        assert "ctp" in pipe._sources


class TestRegistry:
    """Tests for the FetchRegistry."""

    def test_registry_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            reg_path = Path(tmpdir) / "registry.json"

            # Write
            reg = FetchRegistry(path=reg_path)
            assert not reg.is_fetched("doc:001")
            reg.mark_fetched("doc:001", source="test")
            assert reg.is_fetched("doc:001")
            assert "doc:001" in reg.list_fetched()
            assert len(reg) == 1

            # Read back
            reg2 = FetchRegistry(path=reg_path)
            assert reg2.is_fetched("doc:001")
            assert not reg2.is_fetched("doc:999")

    def test_registry_contains(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = FetchRegistry(path=Path(tmpdir) / "reg.json")
            reg.mark_fetched("abc", source="test")
            assert "abc" in reg
            assert "xyz" not in reg

    def test_registry_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = FetchRegistry(path=Path(tmpdir) / "reg.json")
            reg.mark_fetched("a", source="test")
            reg.mark_fetched("b", source="test")
            assert len(reg) == 2
            reg.clear()
            assert len(reg) == 0
