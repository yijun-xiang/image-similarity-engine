import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
import redis.asyncio as redis
from collections import defaultdict
import heapq
import logging

logger = logging.getLogger(__name__)


class LFUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.freq = defaultdict(int)
        self.min_freq = 0
        self.freq_to_keys = defaultdict(set)
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        
        self._update_freq(key)
        return self.cache[key]
    
    def put(self, key: str, value: Any):
        if self.capacity <= 0:
            return
        
        if key in self.cache:
            self.cache[key] = value
            self._update_freq(key)
            return
        
        if len(self.cache) >= self.capacity:
            self._evict()
        
        self.cache[key] = value
        self.freq[key] = 1
        self.freq_to_keys[1].add(key)
        self.min_freq = 1
    
    def _update_freq(self, key: str):
        freq = self.freq[key]
        self.freq[key] += 1
        self.freq_to_keys[freq].remove(key)
        
        if not self.freq_to_keys[freq]:
            del self.freq_to_keys[freq]
            if freq == self.min_freq:
                self.min_freq += 1
        
        self.freq_to_keys[freq + 1].add(key)
    
    def _evict(self):
        key = next(iter(self.freq_to_keys[self.min_freq]))
        self.freq_to_keys[self.min_freq].remove(key)
        
        if not self.freq_to_keys[self.min_freq]:
            del self.freq_to_keys[self.min_freq]
        
        del self.cache[key]
        del self.freq[key]


class AdvancedCacheService:
    def __init__(self, redis_url: str, cache_size: int = 10000):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache = LFUCache(cache_size)
        self.prefetch_queue = asyncio.Queue(maxsize=1000)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'prefetch_hits': 0,
            'evictions': 0
        }
        self._prefetch_task = None
    
    async def connect(self):
        self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
        await self.redis_client.ping()
        self._prefetch_task = asyncio.create_task(self._prefetch_worker())
        logger.info("Advanced cache service connected")
    
    async def disconnect(self):
        if self._prefetch_task:
            self._prefetch_task.cancel()
        if self.redis_client:
            await self.redis_client.close()
    
    async def get_with_ttl(self, key: str) -> Optional[Tuple[Any, int]]:
        local_result = self.local_cache.get(key)
        if local_result is not None:
            self.stats['hits'] += 1
            return local_result, -1
        
        if self.redis_client:
            try:
                pipeline = self.redis_client.pipeline()
                pipeline.get(key)
                pipeline.ttl(key)
                value, ttl = await pipeline.execute()
                
                if value is not None:
                    self.stats['hits'] += 1
                    deserialized = json.loads(value)
                    self.local_cache.put(key, deserialized)
                    return deserialized, ttl
            except Exception as e:
                logger.error(f"Cache get error: {str(e)}")
        
        self.stats['misses'] += 1
        return None, -1
    
    async def set_with_priority(self, key: str, value: Any, ttl: int, priority: int = 0):
        serialized = json.dumps(value, default=str)
        
        if self.redis_client:
            try:
                pipeline = self.redis_client.pipeline()
                pipeline.setex(key, ttl, serialized)
                pipeline.zadd(f"cache:priority", {key: priority})
                await pipeline.execute()
                
                self.local_cache.put(key, value)
            except Exception as e:
                logger.error(f"Cache set error: {str(e)}")
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        results = {}
        redis_keys = []
        
        for key in keys:
            local_result = self.local_cache.get(key)
            if local_result is not None:
                results[key] = local_result
                self.stats['hits'] += 1
            else:
                redis_keys.append(key)
        
        if redis_keys and self.redis_client:
            try:
                values = await self.redis_client.mget(redis_keys)
                for key, value in zip(redis_keys, values):
                    if value is not None:
                        deserialized = json.loads(value)
                        results[key] = deserialized
                        self.local_cache.put(key, deserialized)
                        self.stats['hits'] += 1
                    else:
                        self.stats['misses'] += 1
            except Exception as e:
                logger.error(f"Batch get error: {str(e)}")
                self.stats['misses'] += len(redis_keys)
        
        return results
    
    async def warm_cache(self, pattern: str, limit: int = 1000):
        if not self.redis_client:
            return
        
        try:
            cursor = b'0'
            warmed = 0
            
            while cursor != 0 and warmed < limit:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    values = await self.redis_client.mget(keys)
                    for key, value in zip(keys, values):
                        if value is not None:
                            try:
                                deserialized = json.loads(value)
                                self.local_cache.put(key.decode(), deserialized)
                                warmed += 1
                            except:
                                pass
            
            logger.info(f"Warmed {warmed} cache entries")
        except Exception as e:
            logger.error(f"Cache warming error: {str(e)}")
    
    async def prefetch(self, keys: List[str]):
        for key in keys:
            try:
                await self.prefetch_queue.put(key)
            except asyncio.QueueFull:
                pass
    
    async def _prefetch_worker(self):
        while True:
            try:
                keys_batch = []
                
                try:
                    key = await asyncio.wait_for(self.prefetch_queue.get(), timeout=1.0)
                    keys_batch.append(key)
                    
                    while len(keys_batch) < 50 and not self.prefetch_queue.empty():
                        keys_batch.append(self.prefetch_queue.get_nowait())
                except asyncio.TimeoutError:
                    continue
                
                if keys_batch:
                    await self.batch_get(keys_batch)
                    self.stats['prefetch_hits'] += len(keys_batch)
                    
            except Exception as e:
                logger.error(f"Prefetch worker error: {str(e)}")
                await asyncio.sleep(1)
    
    async def invalidate_pattern(self, pattern: str):
        if not self.redis_client:
            return
        
        try:
            cursor = b'0'
            deleted = 0
            
            while cursor != 0:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    await self.redis_client.delete(*keys)
                    deleted += len(keys)
            
            logger.info(f"Invalidated {deleted} cache entries")
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'local_cache_size': len(self.local_cache.cache)
        }
