"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import models, blocks, simulation, import_export
from .api.websocket import router as ws_router
from .config import settings

app = FastAPI(
    title="LibreSim API",
    description="Backend API for LibreSim block diagram simulation tool",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(blocks.router, prefix="/api/blocks", tags=["blocks"])
app.include_router(simulation.router, prefix="/api/simulate", tags=["simulation"])
app.include_router(import_export.router, prefix="/api/import", tags=["import"])
app.include_router(ws_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "LibreSim API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
