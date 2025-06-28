import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import aioredis
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


class ConnectionPool:
    def __init__(self, pool_config: Dict[str, Any]):
        self.pool_config = pool_config
        self.qdrant_pools: Dict[str, AsyncQdrantClient] = {}
        self.redis_pool: Optional[aioredis.ConnectionPool] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        settings = get_settings()
        
        self.redis_pool = aioredis.ConnectionPool.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
            max_connections=self.pool_config.get('redis_max_connections', 100),
            decode_responses=True
        )
        
        for i in range(self.pool_config.get('qdrant_pool_size', 10)):
            client = AsyncQdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                grpc_port=settings.qdrant_grpc_port,
                prefer_grpc=True,
                limits=models.ChannelPoolSettings(
                    max_concurrent_streams=100,
                    keepalive_time_ms=10000,
                    keepalive_timeout_ms=5000
                )
            )
            self.qdrant_pools[f"client_{i}"] = client
        
        logger.info(f"Initialized connection pools: {len(self.qdrant_pools)} Qdrant clients")
    
    @asynccontextmanager
    async def get_qdrant_client(self):
        async with self._lock:
            client_id = f"client_{hash(asyncio.current_task()) % len(self.qdrant_pools)}"
            client = self.qdrant_pools[client_id]
        
        try:
            yield client
        finally:
            pass
    
    @asynccontextmanager
    async def get_redis_client(self):
        client = aioredis.Redis(connection_pool=self.redis_pool)
        try:
            yield client
        finally:
            await client.close()
    
    async def close(self):
        for client in self.qdrant_pools.values():
            await client.close()
        
        if self.redis_pool:
            await self.redis_pool.disconnect()
        
        logger.info("Connection pools closed")
    
    async def health_check(self) -> Dict[str, Any]:
        health = {
            'qdrant_pools': {},
            'redis_pool': {}
        }
        
        for client_id, client in self.qdrant_pools.items():
            try:
                await client.get_collections()
                health['qdrant_pools'][client_id] = 'healthy'
            except Exception as e:
                health['qdrant_pools'][client_id] = f'unhealthy: {str(e)}'
        
        try:
            async with self.get_redis_client() as redis:
                await redis.ping()
            health['redis_pool'] = {
                'status': 'healthy',
                'active_connections': self.redis_pool._created_connections,
                'available_connections': self.redis_pool._available_connections.qsize()
            }
        except Exception as e:
            health['redis_pool'] = f'unhealthy: {str(e)}'
        
        return health


_connection_pool: Optional[ConnectionPool] = None


async def get_connection_pool() -> ConnectionPool:
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool({
            'qdrant_pool_size': 10,
            'redis_max_connections': 100
        })
        await _connection_pool.initialize()
    return _connection_pool
