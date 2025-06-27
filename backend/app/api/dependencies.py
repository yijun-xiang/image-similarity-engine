from fastapi import Depends
from app.services.ml_service_with_metrics import get_ml_service, MLService
from app.services.vector_service import get_vector_service, VectorService
from app.services.cache_service import get_cache_service, CacheService
from app.config import get_settings, Settings


async def get_ml_service_dep() -> MLService:
    service = get_ml_service()
    await service.load_model()
    return service


async def get_vector_service_dep() -> VectorService:
    service = get_vector_service()
    await service.connect()
    return service


async def get_cache_service_dep() -> CacheService:
    service = get_cache_service()
    await service.connect()
    return service


def get_settings_dep() -> Settings:
    return get_settings()
