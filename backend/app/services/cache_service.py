import asyncio
import json
import logging
import hashlib
from typing import Any, Optional, List
from functools import lru_cache
import redis.asyncio as redis
from datetime import timedelta

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        logger.info("Cache service initialized")
    
    async def connect(self):
        if self.redis_client is not None:
            return
        
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )
            
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        
        hash_object = hashlib.md5(content.encode())
        return f"{prefix}:{hash_object.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        if self.redis_client is None:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {str(e)}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        if self.redis_client is None:
            await self.connect()
        
        try:
            ttl = ttl or settings.cache_ttl
            serialized_value = json.dumps(value, default=str)
            
            result = await self.redis_client.setex(
                key, 
                timedelta(seconds=ttl),
                serialized_value
            )
            return result
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        if self.redis_client is None:
            await self.connect()
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {str(e)}")
            return False
    
    async def get_search_cache(self, image_data: str) -> Optional[List[dict]]:
        cache_key = self._generate_cache_key("search", image_data)
        return await self.get(cache_key)
    
    async def set_search_cache(
        self, 
        image_data: str, 
        results: List[dict], 
        ttl: Optional[int] = None
    ) -> bool:
        cache_key = self._generate_cache_key("search", image_data)
        return await self.set(cache_key, results, ttl)
    
    async def get_feature_cache(self, image_data: str) -> Optional[List[float]]:
        cache_key = self._generate_cache_key("features", image_data)
        return await self.get(cache_key)
    
    async def set_feature_cache(
        self, 
        image_data: str, 
        features: List[float], 
        ttl: Optional[int] = None
    ) -> bool:
        cache_key = self._generate_cache_key("features", image_data)
        return await self.set(cache_key, features, ttl)
    
    async def clear_all(self) -> bool:
        if self.redis_client is None:
            await self.connect()
        
        try:
            await self.redis_client.flushdb()
            logger.info("All cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return False
    
    async def get_stats(self) -> dict:
        if self.redis_client is None:
            await self.connect()
        
        try:
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {}


@lru_cache()
def get_cache_service() -> CacheService:
    return CacheService()
