import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import get_settings
from app.utils.logging import setup_logging
from app.api.endpoints import search, health, batch
from app.services.ml_service import get_ml_service
from app.services.vector_service import get_vector_service
from app.services.cache_service import get_cache_service

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Image Similarity Search Engine...")
    
    try:
        logger.info("Loading ML model...")
        ml_service = get_ml_service()
        await ml_service.load_model()
        
        logger.info("Connecting to vector database...")
        try:
            vector_service = get_vector_service()
            await vector_service.connect()
        except Exception as e:
            logger.warning(f"Vector database connection failed: {str(e)} - continuing without it")
        
        logger.info("Connecting to cache service...")
        try:
            cache_service = get_cache_service()
            await cache_service.connect()
        except Exception as e:
            logger.warning(f"Cache service connection failed: {str(e)} - continuing without it")
        
        logger.info("All available services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise
    
    yield
    
    logger.info("Shutting down services...")


app = FastAPI(
    title=settings.app_name,
    description="High-performance image similarity search engine using CLIP and Qdrant",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

app.include_router(
    search.router,
    prefix=settings.api_prefix,
    tags=["Search"]
)

app.include_router(
    health.router,
    prefix=settings.api_prefix,
    tags=["Health"]
)

app.include_router(
    batch.router,
    prefix=settings.api_prefix,
    tags=["Batch"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An internal error occurred"
        }
    )


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
