"""FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import embed, search, compare, health, models

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Phil API", version="0.1.0",
              description="REST API for the Phil philosophy research ecosystem",
              lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

app.include_router(embed.router, tags=["embed"])
app.include_router(search.router, tags=["search"])
app.include_router(compare.router, tags=["compare"])
app.include_router(health.router, tags=["health"])
app.include_router(models.router, tags=["models"])
