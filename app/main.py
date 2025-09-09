import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.models.responses import HealthResponse, ConfigResponse
from app.api import risk, shelters, tiles

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Tokyo Disaster Entrapment Anticipation API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.version
    )


@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get runtime configuration."""
    return ConfigResponse(
        mode=settings.mode,
        version=settings.version,
        features={
            "database": settings.mode == "postgis",
            "local_mode": settings.mode == "local",
            "tiles": True,
            "shelters": True
        }
    )


app.include_router(risk.router, prefix="/risk", tags=["risk"])
app.include_router(shelters.router, prefix="/shelters", tags=["shelters"])
app.include_router(tiles.router, prefix="/tiles", tags=["tiles"])

# Mount static files last to avoid conflicts with API routes
web_dir = Path("web")
if web_dir.exists():
    app.mount("/static", StaticFiles(directory="web"), name="static")
    # Serve index.html at root for convenience
    from fastapi.responses import FileResponse
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse("web/index.html")

# Mount data files for frontend access
data_dir = Path("data")
if data_dir.exists():
    app.mount("/data", StaticFiles(directory="data"), name="data")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)