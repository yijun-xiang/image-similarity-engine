import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import get_settings
from app.models.schemas import SimilarImage

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorService:
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collection_name = settings.qdrant_collection_name
        self.vector_size = 512
        logger.info("Vector service initialized")
    
    async def connect(self):
        if self.client is not None:
            return
        
        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=settings.search_timeout,
                check_compatibility=False
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_collections
            )
            
            logger.info(f"Connected to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
            
            await self.ensure_collection()
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise
    
    async def ensure_collection(self):
        try:
            collections = await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_collections
            )
            
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections.collections
            )
            
            if not collection_exists:
                logger.info(f"Creating collection: {self.collection_name}")
                await self._create_collection()
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection: {str(e)}")
            raise
    
    async def _create_collection(self):
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
        )
        logger.info(f"Collection {self.collection_name} created successfully")
    
    async def insert_vectors(
        self,
        vectors: List[np.ndarray],
        image_ids: List[str],
        metadata: List[Dict[str, Any]] = None
    ) -> List[str]:
        if self.client is None:
            await self.connect()
        
        if metadata is None:
            metadata = [{}] * len(vectors)
        
        try:
            points = []
            point_ids = []
            
            for i, (vector, image_id, meta) in enumerate(zip(vectors, image_ids, metadata)):
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)
                
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=vector.tolist(),
                        payload={
                            "image_id": image_id,
                            "metadata": meta,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    )
                )
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
            )
            
            logger.info(f"Inserted {len(points)} vectors successfully")
            return point_ids
            
        except Exception as e:
            logger.error(f"Failed to insert vectors: {str(e)}")
            raise
    
    async def search_similar(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        threshold: float = 0.0,
        include_metadata: bool = True
    ) -> List[SimilarImage]:
        if self.client is None:
            await self.connect()
        
        try:
            search_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector.tolist(),
                    limit=top_k,
                    score_threshold=threshold,
                    with_payload=True
                )
            )
            
            results = []
            for scored_point in search_result:
                payload = scored_point.payload or {}
                
                result = SimilarImage(
                    image_id=payload.get("image_id", "unknown"),
                    score=scored_point.score,
                    metadata=payload.get("metadata", {}) if include_metadata else None
                )
                results.append(result)
            
            logger.debug(f"Found {len(results)} similar images")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    async def delete_by_image_id(self, image_id: str) -> bool:
        if self.client is None:
            await self.connect()
        
        try:
            search_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="image_id",
                                match=models.MatchValue(value=image_id)
                            )
                        ]
                    ),
                    limit=100,
                    with_payload=False
                )
            )
            
            point_ids = [point.id for point in search_result[0]]
            
            if point_ids:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.delete(
                        collection_name=self.collection_name,
                        points_selector=models.PointIdsList(points=point_ids)
                    )
                )
                logger.info(f"Deleted {len(point_ids)} points for image_id: {image_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete image {image_id}: {str(e)}")
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        if self.client is None:
            await self.connect()
        
        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.get_collection(self.collection_name)
            )
            
            return {
                "name": self.collection_name,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance.value,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            raise


@lru_cache()
def get_vector_service() -> VectorService:
    return VectorService()
