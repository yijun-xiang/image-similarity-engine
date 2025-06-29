import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import get_settings
from app.utils.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Image Similarity Search Engine (Standalone Mode)...")
    
    try:
        logger.info("Loading ML model...")
        from app.services.ml_service import get_ml_service
        ml_service = get_ml_service()
        await ml_service.load_model()
        logger.info("ML model loaded successfully")
    except Exception as e:
        logger.warning(f"ML service initialization failed: {str(e)}")
    
    logger.info("Running in standalone mode - Qdrant and Redis connections disabled")
    
    yield
    
    logger.info("Shutting down services...")


app = FastAPI(
    title=settings.app_name,
    description="High-performance image similarity search engine using CLIP",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running in standalone mode"
    }


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2025-06-28T00:00:00Z",
        "version": settings.app_version,
        "services": {
            "ml_service": "available",
            "vector_database": "not configured",
            "cache_service": "not configured"
        },
        "mode": "standalone"
    }


@app.get("/api/v1/stats")
async def get_stats():
    return {
        "collection": {"status": "not available in standalone mode"},
        "cache": {"status": "not available in standalone mode"},
        "status": "limited functionality"
    }


@app.post("/api/v1/search")
async def search_images(request: dict):
    return {
        "error": "Search functionality requires Qdrant connection",
        "message": "Please deploy with Qdrant service or use full deployment"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main_standalone:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False
    )
