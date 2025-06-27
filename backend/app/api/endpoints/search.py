import time
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.schemas import (
    SearchRequest, SearchResponse, SimilarImage,
    ImageUpload, IndexResponse, ErrorResponse
)
from app.services.ml_service import MLService
from app.services.vector_service import VectorService
from app.services.cache_service import CacheService
from app.api.dependencies import (
    get_ml_service_dep, get_vector_service_dep, get_cache_service_dep
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_similar_images(
    request: SearchRequest,
    ml_service: MLService = Depends(get_ml_service_dep),
    vector_service: VectorService = Depends(get_vector_service_dep),
    cache_service: CacheService = Depends(get_cache_service_dep)
):
    start_time = time.time()
    query_id = str(uuid.uuid4())
    
    try:
        cached_results = await cache_service.get_search_cache(request.image_data)
        if cached_results:
            logger.info(f"Cache hit for query {query_id}")
            return SearchResponse(
                query_id=query_id,
                results=[SimilarImage(**result) for result in cached_results[:request.top_k]],
                total_found=len(cached_results),
                search_time_ms=(time.time() - start_time) * 1000,
                cached=True
            )
        
        logger.info(f"Extracting features for query {query_id}")
        features = await ml_service.extract_features(request.image_data)
        
        logger.info(f"Searching similar images for query {query_id}")
        results = await vector_service.search_similar(
            query_vector=features,
            top_k=request.top_k,
            threshold=request.threshold,
            include_metadata=request.include_metadata
        )
        
        async def cache_results():
            try:
                await cache_service.set_search_cache(
                    request.image_data, 
                    [result.dict() for result in results]
                )
            except Exception as e:
                logger.error(f"Failed to cache results: {str(e)}")
        
        import asyncio
        asyncio.create_task(cache_results())
        
        search_time = (time.time() - start_time) * 1000
        logger.info(f"Query {query_id} completed in {search_time:.2f}ms, found {len(results)} results")
        
        return SearchResponse(
            query_id=query_id,
            results=results,
            total_found=len(results),
            search_time_ms=search_time,
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Search failed for query {query_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/index", response_model=IndexResponse)
async def index_image(
    request: ImageUpload,
    ml_service: MLService = Depends(get_ml_service_dep),
    vector_service: VectorService = Depends(get_vector_service_dep)
):
    start_time = time.time()
    image_id = request.image_id or str(uuid.uuid4())
    
    try:
        logger.info(f"Indexing image {image_id}")
        
        features = await ml_service.extract_features(request.image_data)
        
        await vector_service.insert_vectors(
            vectors=[features],
            image_ids=[image_id],
            metadata=[request.metadata]
        )
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Image {image_id} indexed successfully in {processing_time:.2f}ms")
        
        return IndexResponse(
            image_id=image_id,
            success=True,
            message="Image indexed successfully",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Failed to index image {image_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(e)}"
        )


@router.delete("/index/{image_id}")
async def delete_image(
    image_id: str,
    vector_service: VectorService = Depends(get_vector_service_dep)
):
    try:
        success = await vector_service.delete_by_image_id(image_id)
        
        if success:
            return {"message": f"Image {image_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Image {image_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete image {image_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Deletion failed: {str(e)}"
        )


@router.get("/stats")
async def get_search_stats(
    vector_service: VectorService = Depends(get_vector_service_dep),
    cache_service: CacheService = Depends(get_cache_service_dep)
):
    try:
        collection_info = await vector_service.get_collection_info()
        cache_stats = await cache_service.get_stats()
        
        return {
            "collection": collection_info,
            "cache": cache_stats,
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
