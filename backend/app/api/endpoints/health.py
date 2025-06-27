import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from app.models.schemas import HealthResponse
from app.services.ml_service import get_ml_service
from app.services.vector_service import get_vector_service
from app.services.cache_service import get_cache_service
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    services_status = {}
    
    try:
        ml_service = get_ml_service()
        await ml_service.load_model()
        services_status["ml_service"] = "healthy"
    except Exception as e:
        logger.error(f"ML service health check failed: {str(e)}")
        services_status["ml_service"] = "unhealthy"
    
    try:
        vector_service = get_vector_service()
        await vector_service.connect()
        services_status["vector_database"] = "healthy"
    except Exception as e:
        logger.error(f"Vector database health check failed: {str(e)}")
        services_status["vector_database"] = "unhealthy"
    
    try:
        cache_service = get_cache_service()
        await cache_service.connect()
        services_status["cache_service"] = "healthy"
    except Exception as e:
        logger.error(f"Cache service health check failed: {str(e)}")
        services_status["cache_service"] = "unhealthy"
    
    overall_status = "healthy" if all(
        status == "healthy" for status in services_status.values()
    ) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version=settings.app_version,
        services=services_status
    )


@router.get("/ready")
async def readiness_check():
    try:
        tasks = [
            _check_ml_service(),
            _check_vector_service(),
            _check_cache_service()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        if any(isinstance(result, Exception) for result in results):
            return {"status": "not_ready"}, 503
        
        return {"status": "ready"}
    
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {"status": "not_ready", "error": str(e)}, 503


async def _check_ml_service():
    ml_service = get_ml_service()
    await ml_service.load_model()


async def _check_vector_service():
    vector_service = get_vector_service()
    await vector_service.connect()


async def _check_cache_service():
    cache_service = get_cache_service()
    await cache_service.connect()
