"""Models listing endpoint."""
from fastapi import APIRouter
from philengine.registry import BackendRegistry

router = APIRouter()

@router.get("/models")
async def list_models():
    return {"backends": BackendRegistry.available()}
