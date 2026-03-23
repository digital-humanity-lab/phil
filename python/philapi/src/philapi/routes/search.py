"""Search endpoint."""
from fastapi import APIRouter, Depends
from ..schemas import SearchRequest, SearchResponse
from ..dependencies import get_engine

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_concepts(req: SearchRequest, engine=Depends(get_engine)):
    return SearchResponse(results=[], query=req.query, model="default")
