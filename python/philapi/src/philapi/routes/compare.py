"""Compare endpoint."""
from fastapi import APIRouter, Depends
from ..schemas import CompareRequest, CompareResponse
from ..dependencies import get_engine

router = APIRouter()

@router.post("/compare", response_model=CompareResponse)
async def compare_concepts(req: CompareRequest, engine=Depends(get_engine)):
    sim = engine.similarity(req.concept_a, req.concept_b)
    return CompareResponse(similarity=sim, method=req.method)
