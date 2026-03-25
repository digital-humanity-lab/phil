"""philcorpus - Data acquisition pipeline for philosophical text corpora."""

from philcorpus.pipeline import CorpusPipeline
from philcorpus.sources.openalex import fetch_oa_papers
from philcorpus.sources.jstage import fetch_jstage
from philcorpus.sources.gutenberg import fetch_gutenberg
from philcorpus.sources.ctp import fetch_ctp
from philcorpus.sources.aozora import fetch_aozora

__version__ = "0.1.0"

__all__ = [
    "CorpusPipeline",
    "fetch_oa_papers",
    "fetch_jstage",
    "fetch_gutenberg",
    "fetch_ctp",
    "fetch_aozora",
]
