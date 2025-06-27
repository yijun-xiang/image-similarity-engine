import time
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
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
from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    vector_search_results,
    indexed_images_total,
    cache_hits_total,
    cache_misses_total,
    errors_total,
    active_requests,
    track_vector_search,
    track_cache_operation
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_similar_images(
    request: SearchRequest,
    req: Request,
    ml_service: MLService = Depends(get_ml_service_dep),
    vector_service: VectorService = Depends(get_vector_service_dep),
    cache_service: CacheService = Depends(get_cache_service_dep)
):
    start_time = time.time()
    query_id = str(uuid.uuid4())
    
    active_requests.inc()
    
    try:
        http_requests_total.labels(
            method="POST",
            endpoint="/api/v1/search",
            status="processing"
        ).inc()
        
        cached_results = await cache_service.get_search_cache(request.image_data)
        if cached_results:
            logger.info(f"Cache hit for query {query_id}")
            cache_hits_total.labels(cache_type="search").inc()
            
            response = SearchResponse(
                query_id=query_id,
                results=[SimilarImage(**result) for result in cached_results[:request.top_k]],
                total_found=len(cached_results),
                search_time_ms=(time.time() - start_time) * 1000,
                cached=True
            )
            
            http_requests_total.labels(
                method="POST",
                endpoint="/api/v1/search",
                status="200"
            ).inc()
            
            return response
        else:
            cache_misses_total.labels(cache_type="search").inc()
        
        logger.info(f"Extracting features for query {query_id}")
        features = await ml_service.extract_features(request.image_data)
        
        logger.info(f"Searching similar images for query {query_id}")
        
        @track_vector_search()
        async def search_with_metrics():
            return await vector_service.search_similar(
                query_vector=features,
                top_k=request.top_k,
                threshold=request.threshold,
                include_metadata=request.include_metadata
            )
        
        results = await search_with_metrics()
        
        vector_search_results.observe(len(results))
        
        async def cache_results():
            try:
                @track_cache_operation("set")
                async def set_cache():
                    return await cache_service.set_search_cache(
                        request.image_data, 
                        [result.dict() for result in results]
                    )
                await set_cache()
            except Exception as e:
                logger.error(f"Failed to cache results: {str(e)}")
        
        import asyncio
        asyncio.create_task(cache_results())
        
        search_time = (time.time() - start_time) * 1000
        logger.info(f"Query {query_id} completed in {search_time:.2f}ms, found {len(results)} results")
        
        http_request_duration_seconds.labels(
            method="POST",
            endpoint="/api/v1/search"
        ).observe(search_time / 1000)
        
        http_requests_total.labels(
            method="POST",
            endpoint="/api/v1/search",
            status="200"
        ).inc()
        
        return SearchResponse(
            query_id=query_id,
            results=results,
            total_found=len(results),
            search_time_ms=search_time,
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Search failed for query {query_id}: {str(e)}")
        
        errors_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/search"
        ).inc()
        
        http_requests_total.labels(
            method="POST",
            endpoint="/api/v1/search",
            status="500"
        ).inc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    finally:
        active_requests.dec()
        
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method="POST",
            endpoint="/api/v1/search"
        ).observe(duration)


@router.post("/index", response_model=IndexResponse)
async def index_image(
    request: ImageUpload,
    req: Request,
    ml_service: MLService = Depends(get_ml_service_dep),
    vector_service: VectorService = Depends(get_vector_service_dep)
):
    start_time = time.time()
    image_id = request.image_id or str(uuid.uuid4())
    
    active_requests.inc()
    
    try:
        http_requests_total.labels(
            method="POST",
            endpoint="/api/v1/index",
            status="processing"
        ).inc()
        
        logger.info(f"Indexing image {image_id}")
        
        features = await ml_service.extract_features(request.image_data)
        
        await vector_service.insert_vectors(
            vectors=[features],
            image_ids=[image_id],
            metadata=[request.metadata]
        )
        
        indexed_images_total.inc()
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Image {image_id} indexed successfully in {processing_time:.2f}ms")
        
        http_requests_total.labels(
            method="POST",
            endpoint="/api/v1/index",
            status="200"
        ).inc()
        
        return IndexResponse(
            image_id=image_id,
            success=True,
            message="Image indexed successfully",
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Failed to index image {image_id}: {str(e)}")
        
        errors_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/index"
        ).inc()
        
        http_requests_total.labels(
            method="POST",
            endpoint="/api/v1/index",
            status="500"
        ).inc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(e)}"
        )
    finally:
        active_requests.dec()
        
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method="POST",
            endpoint="/api/v1/index"
        ).observe(duration)


@router.delete("/index/{image_id}")
async def delete_image(
    image_id: str,
    req: Request,
    vector_service: VectorService = Depends(get_vector_service_dep)
):
    start_time = time.time()
    
    active_requests.inc()
    
    try:
        http_requests_total.labels(
            method="DELETE",
            endpoint="/api/v1/index/{image_id}",
            status="processing"
        ).inc()
        
        success = await vector_service.delete_by_image_id(image_id)
        
        if success:
            indexed_images_total.dec()
            
            http_requests_total.labels(
                method="DELETE",
                endpoint="/api/v1/index/{image_id}",
                status="200"
            ).inc()
            
            return {"message": f"Image {image_id} deleted successfully"}
        else:
            http_requests_total.labels(
                method="DELETE",
                endpoint="/api/v1/index/{image_id}",
                status="404"
            ).inc()
            
            raise HTTPException(
                status_code=404,
                detail=f"Image {image_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete image {image_id}: {str(e)}")
        
        errors_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/index/{image_id}"
        ).inc()
        
        http_requests_total.labels(
            method="DELETE",
            endpoint="/api/v1/index/{image_id}",
            status="500"
        ).inc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Deletion failed: {str(e)}"
        )
    finally:
        active_requests.dec()
        
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method="DELETE",
            endpoint="/api/v1/index/{image_id}"
        ).observe(duration)


@router.get("/stats")
async def get_search_stats(
    req: Request,
    vector_service: VectorService = Depends(get_vector_service_dep),
    cache_service: CacheService = Depends(get_cache_service_dep)
):
    start_time = time.time()
    
    active_requests.inc()
    
    try:
        http_requests_total.labels(
            method="GET",
            endpoint="/api/v1/stats",
            status="processing"
        ).inc()
        
        collection_info = await vector_service.get_collection_info()
        cache_stats = await cache_service.get_stats()
        
        indexed_images_total.set(collection_info.get("points_count", 0))
        
        http_requests_total.labels(
            method="GET",
            endpoint="/api/v1/stats",
            status="200"
        ).inc()
        
        return {
            "collection": collection_info,
            "cache": cache_stats,
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        
        errors_total.labels(
            error_type=type(e).__name__,
            endpoint="/api/v1/stats"
        ).inc()
        
        http_requests_total.labels(
            method="GET",
            endpoint="/api/v1/stats",
            status="500"
        ).inc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
    finally:
        active_requests.dec()
        
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method="GET",
            endpoint="/api/v1/stats"
        ).observe(duration)
