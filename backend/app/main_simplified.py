import asyncio
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
    logger.info("Starting Image Similarity Search Engine (Simplified)...")
    yield
    logger.info("Shutting down services...")


app = FastAPI(
    title=settings.app_name,
    description="High-performance image similarity search engine",
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
        "status": "running"
    }


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "services": {
            "api": "running",
            "ml": "disabled",
            "vector_db": "disabled",
            "cache": "disabled"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main_simplified:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
