import hashlib
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
import asyncio
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class ShardingService:
    def __init__(self, shard_configs: List[Dict[str, Any]]):
        self.shards: List[QdrantClient] = []
        self.shard_count = len(shard_configs)
        self.shard_configs = shard_configs
        self._initialize_shards()
    
    def _initialize_shards(self):
        for config in self.shard_configs:
            client = QdrantClient(
                host=config['host'],
                port=config['port'],
                timeout=30,
                grpc_port=config.get('grpc_port', 6334),
                prefer_grpc=True
            )
            self.shards.append(client)
            logger.info(f"Initialized shard: {config['host']}:{config['port']}")
    
    def _get_shard_index(self, image_id: str) -> int:
        hash_value = int(hashlib.md5(image_id.encode()).hexdigest(), 16)
        return hash_value % self.shard_count
    
    async def create_collections(self, collection_name: str, vector_size: int):
        tasks = []
        for i, shard in enumerate(self.shards):
            task = asyncio.create_task(self._create_collection_on_shard(
                shard, f"{collection_name}_shard_{i}", vector_size
            ))
            tasks.append(task)
        await asyncio.gather(*tasks)
    
    async def _create_collection_on_shard(self, shard: QdrantClient, collection_name: str, vector_size: int):
        try:
            collections = await asyncio.get_event_loop().run_in_executor(
                None, shard.get_collections
            )
            
            if not any(col.name == collection_name for col in collections.collections):
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: shard.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=vector_size,
                            distance=models.Distance.COSINE,
                            on_disk=True
                        ),
                        hnsw_config=models.HnswConfigDiff(
                            m=32,
                            ef_construct=200,
                            full_scan_threshold=20000
                        ),
                        optimizers_config=models.OptimizersConfigDiff(
                            memmap_threshold=50000,
                            indexing_threshold=30000,
                            flush_interval_sec=30
                        ),
                        quantization_config=models.ScalarQuantization(
                            scalar=models.ScalarQuantizationConfig(
                                type=models.ScalarType.INT8,
                                quantile=0.99,
                                always_ram=False
                            )
                        )
                    )
                )
                logger.info(f"Created collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {str(e)}")
            raise
    
    async def insert_vectors(self, vectors: List[np.ndarray], image_ids: List[str], metadata: List[Dict[str, Any]]):
        shard_batches = {}
        
        for i, (vector, image_id, meta) in enumerate(zip(vectors, image_ids, metadata)):
            shard_idx = self._get_shard_index(image_id)
            if shard_idx not in shard_batches:
                shard_batches[shard_idx] = {
                    'vectors': [],
                    'image_ids': [],
                    'metadata': []
                }
            shard_batches[shard_idx]['vectors'].append(vector)
            shard_batches[shard_idx]['image_ids'].append(image_id)
            shard_batches[shard_idx]['metadata'].append(meta)
        
        tasks = []
        for shard_idx, batch in shard_batches.items():
            task = asyncio.create_task(self._insert_batch_to_shard(
                shard_idx, batch['vectors'], batch['image_ids'], batch['metadata']
            ))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _insert_batch_to_shard(self, shard_idx: int, vectors: List[np.ndarray], 
                                     image_ids: List[str], metadata: List[Dict[str, Any]]):
        points = []
        for vector, image_id, meta in zip(vectors, image_ids, metadata):
            points.append(
                models.PointStruct(
                    id=hashlib.md5(image_id.encode()).hexdigest()[:16],
                    vector=vector.tolist(),
                    payload={
                        "image_id": image_id,
                        "metadata": meta,
                        "shard": shard_idx
                    }
                )
            )
        
        collection_name = f"{self.shard_configs[0]['collection']}_shard_{shard_idx}"
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.shards[shard_idx].upsert(
                collection_name=collection_name,
                points=points,
                wait=False
            )
        )
    
    async def search_similar(self, query_vector: np.ndarray, top_k: int = 10, 
                           threshold: float = 0.0) -> List[Dict[str, Any]]:
        tasks = []
        for i, shard in enumerate(self.shards):
            collection_name = f"{self.shard_configs[0]['collection']}_shard_{i}"
            task = asyncio.create_task(self._search_shard(
                shard, collection_name, query_vector, top_k * 2, threshold
            ))
            tasks.append(task)
        
        shard_results = await asyncio.gather(*tasks)
        
        all_results = []
        for results in shard_results:
            all_results.extend(results)
        
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        return all_results[:top_k]
    
    async def _search_shard(self, shard: QdrantClient, collection_name: str, 
                          query_vector: np.ndarray, limit: int, threshold: float) -> List[Dict[str, Any]]:
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: shard.search(
                    collection_name=collection_name,
                    query_vector=query_vector.tolist(),
                    limit=limit,
                    score_threshold=threshold,
                    with_payload=True
                )
            )
            
            return [
                {
                    'image_id': point.payload.get('image_id'),
                    'score': point.score,
                    'metadata': point.payload.get('metadata', {}),
                    'shard': point.payload.get('shard')
                }
                for point in results
            ]
        except Exception as e:
            logger.error(f"Search failed on shard {collection_name}: {str(e)}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        stats = {
            'total_shards': self.shard_count,
            'shards': []
        }
        
        for i, shard in enumerate(self.shards):
            collection_name = f"{self.shard_configs[0]['collection']}_shard_{i}"
            try:
                info = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: shard.get_collection(collection_name)
                )
                stats['shards'].append({
                    'shard_id': i,
                    'host': self.shard_configs[i]['host'],
                    'points_count': info.points_count,
                    'segments_count': info.segments_count,
                    'status': 'healthy'
                })
            except Exception as e:
                stats['shards'].append({
                    'shard_id': i,
                    'host': self.shard_configs[i]['host'],
                    'status': 'unhealthy',
                    'error': str(e)
                })
        
        return stats


@lru_cache()
def get_sharding_service() -> ShardingService:
    from app.config import get_settings
    settings = get_settings()
    
    shard_configs = []
    for i in range(settings.shard_count):
        shard_configs.append({
            'host': f"{settings.qdrant_host}",
            'port': settings.qdrant_port + i,
            'grpc_port': settings.qdrant_grpc_port + i,
            'collection': settings.qdrant_collection_name
        })
    
    return ShardingService(shard_configs)
