"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, Field

class EmbedRequest(BaseModel):
    texts: list[str]
    model: str = "default"

class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int

class SearchRequest(BaseModel):
    query: str
    traditions: list[str] | None = None
    top_k: int = 10

class SearchResult(BaseModel):
    concept_id: str
    label: str
    similarity: float
    tradition: str
    text_excerpt: str = ""

class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    model: str

class CompareRequest(BaseModel):
    concept_a: str
    concept_b: str
    method: str = "hybrid"

class CompareResponse(BaseModel):
    similarity: float
    method: str
    facet_scores: dict[str, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)

class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: list[str] = Field(default_factory=list)
