from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    app_name: str = "Image Similarity Engine"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    model_name: str = "openai/clip-vit-base-patch32"
    model_cache_dir: str = "./models"
    batch_size: int = 32
    device: str = "auto"
    
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "image_features"
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    max_image_size: int = 10 * 1024 * 1024  
    search_timeout: int = 30
    cache_ttl: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
