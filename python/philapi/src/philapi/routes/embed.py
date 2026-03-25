"""Embedding endpoint."""
from fastapi import APIRouter, Depends
from ..schemas import EmbedRequest, EmbedResponse
from ..dependencies import get_engine

router = APIRouter()

@router.post("/embed", response_model=EmbedResponse)
async def embed_texts(req: EmbedRequest, engine=Depends(get_engine)):
    embeddings = engine.encode(req.texts)
    return EmbedResponse(embeddings=embeddings.tolist(), model=req.model,
                         dimensions=embeddings.shape[1])
