"""Main FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .api.routes import blocks, examples, import_export, models, simulation
from .api.websocket import router as ws_router
from .codegen.controller import router as codegen_router
from .config import settings

# Project root directory - in Docker, mounted at /project; locally, parent of backend/
# Check if running in Docker (where files are mounted at /project)
DOCKER_PROJECT_ROOT = Path("/project")
LOCAL_PROJECT_ROOT = Path(__file__).parent.parent.parent

PROJECT_ROOT = DOCKER_PROJECT_ROOT if DOCKER_PROJECT_ROOT.exists() else LOCAL_PROJECT_ROOT

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
app.include_router(examples.router, prefix="/api/examples", tags=["examples"])
app.include_router(codegen_router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "LibreSim API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/docs/readme", response_class=PlainTextResponse)
async def get_project_readme():
    """Get the project README.md content."""
    readme_path = PROJECT_ROOT / "README.md"
    if not readme_path.exists():
        raise HTTPException(status_code=404, detail="README.md not found")
    return readme_path.read_text(encoding="utf-8")


@app.get("/api/docs/examples", response_class=PlainTextResponse)
async def get_examples_readme():
    """Get the examples/README.md content."""
    readme_path = PROJECT_ROOT / "examples" / "README.md"
    if not readme_path.exists():
        raise HTTPException(status_code=404, detail="examples/README.md not found")
    return readme_path.read_text(encoding="utf-8")
