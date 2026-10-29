from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import CORS_ORIGINS, ensure_directories
from backend.app.database import init_db
from backend.app.routes import health, runs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event to initialize storage directories and database tables."""
    ensure_directories()
    init_db()
    yield


app = FastAPI(
    title="CrowdAhead API",
    description=(
        "Backend REST API for CrowdAhead railway crowd-analysis and management platform. "
        "Provides video upload, CSV detection testing, ByteTrack tracking, "
        "4-zone crowd distribution, movement & flow metrics, and 2D spatial density heatmaps."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(runs.router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    """Welcome endpoint pointing to interactive documentation."""
    return {
        "project": "CrowdAhead",
        "description": "Crowd Detection, Tracking, and Risk Management API",
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
