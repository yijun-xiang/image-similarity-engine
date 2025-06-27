import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from app.tasks.image_tasks import process_batch_images, process_single_image
from app.core.celery_app import celery_app
from app.services.ml_service import MLService
from app.services.vector_service import VectorService
from app.api.dependencies import get_ml_service_dep, get_vector_service_dep

logger = logging.getLogger(__name__)
router = APIRouter()


class BatchImageItem(BaseModel):
    image_data: str
    image_id: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class BatchUploadRequest(BaseModel):
    images: List[BatchImageItem]
    async_processing: bool = True


class BatchJobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    total_images: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    current: Optional[int] = None
    total: Optional[int] = None
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("/batch/upload", response_model=BatchJobResponse)
async def batch_upload_images(
    request: BatchUploadRequest,
    ml_service: MLService = Depends(get_ml_service_dep),
    vector_service: VectorService = Depends(get_vector_service_dep)
):
    try:
        batch_data = []
        for item in request.images:
            batch_data.append({
                "image_data": item.image_data,
                "image_id": item.image_id or str(uuid.uuid4()),
                "metadata": item.metadata
            })
        
        if request.async_processing:
            task = process_batch_images.delay(batch_data)
            
            return BatchJobResponse(
                job_id=task.id,
                status="accepted",
                message=f"Batch job started for {len(batch_data)} images",
                total_images=len(batch_data)
            )
        else:
            # Synchronous processing
            results = []
            successful = 0
            
            for data in batch_data:
                try:
                    features = await ml_service.extract_features(data["image_data"])
                    await vector_service.insert_vectors(
                        vectors=[features],
                        image_ids=[data["image_id"]],
                        metadata=[data["metadata"]]
                    )
                    results.append({
                        "status": "success",
                        "image_id": data["image_id"]
                    })
                    successful += 1
                except Exception as e:
                    results.append({
                        "status": "error",
                        "image_id": data["image_id"],
                        "error": str(e)
                    })
            
            return BatchJobResponse(
                job_id="sync_" + str(uuid.uuid4()),
                status="completed",
                message=f"Processed {successful}/{len(batch_data)} images successfully",
                total_images=len(batch_data)
            )
            
    except Exception as e:
        logger.error(f"Batch upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    try:
        if job_id.startswith("sync_"):
            return JobStatusResponse(
                job_id=job_id,
                status="completed",
                result={"message": "Synchronous job completed"}
            )
        
        task = celery_app.AsyncResult(job_id)
        
        if task.state == "PENDING":
            return JobStatusResponse(
                job_id=job_id,
                status="pending",
                current=0,
                total=0
            )
        elif task.state == "PROCESSING":
            return JobStatusResponse(
                job_id=job_id,
                status="processing",
                current=task.info.get("current", 0),
                total=task.info.get("total", 0)
            )
        elif task.state == "SUCCESS":
            return JobStatusResponse(
                job_id=job_id,
                status="completed",
                result=task.result
            )
        elif task.state == "FAILURE":
            return JobStatusResponse(
                job_id=job_id,
                status="failed",
                error=str(task.info)
            )
        else:
            return JobStatusResponse(
                job_id=job_id,
                status=task.state.lower(),
                current=task.info.get("current", 0) if isinstance(task.info, dict) else None,
                total=task.info.get("total", 0) if isinstance(task.info, dict) else None
            )
            
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/jobs")
async def list_active_jobs():
    try:
        active_tasks = celery_app.control.inspect().active()
        
        if not active_tasks:
            return {"active_jobs": []}
        
        jobs = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                jobs.append({
                    "job_id": task["id"],
                    "name": task["name"],
                    "worker": worker,
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {})
                })
        
        return {"active_jobs": jobs}
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        return {"active_jobs": [], "error": str(e)}


@router.delete("/batch/cancel/{job_id}")
async def cancel_job(job_id: str):
    try:
        celery_app.control.revoke(job_id, terminate=True)
        return {"message": f"Job {job_id} cancelled"}
    except Exception as e:
        logger.error(f"Failed to cancel job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
