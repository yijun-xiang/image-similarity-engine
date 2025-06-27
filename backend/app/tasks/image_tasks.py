import logging
import requests
from typing import List, Dict, Any
from celery import current_task
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000/api/v1"


@celery_app.task(bind=True, name="process_single_image")
def process_single_image(self, image_data: str, image_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    try:
        current_task.update_state(
            state="PROCESSING",
            meta={"status": "Indexing image..."}
        )
        
        response = requests.post(f"{API_BASE_URL}/index", json={
            "image_data": image_data,
            "image_id": image_id,
            "metadata": metadata
        })
        
        if response.status_code == 200:
            return {
                "status": "success",
                "image_id": image_id,
                "message": "Image processed successfully"
            }
        else:
            return {
                "status": "error",
                "image_id": image_id,
                "message": f"API error: {response.status_code}"
            }
        
    except Exception as e:
        logger.error(f"Failed to process image {image_id}: {str(e)}")
        return {
            "status": "error",
            "image_id": image_id,
            "message": str(e)
        }


@celery_app.task(bind=True, name="process_batch_images")
def process_batch_images(self, batch_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        total_images = len(batch_data)
        results = []
        
        for i, item in enumerate(batch_data):
            current_task.update_state(
                state="PROCESSING",
                meta={
                    "current": i,
                    "total": total_images,
                    "status": f"Processing image {i+1}/{total_images}"
                }
            )
            
            response = requests.post(f"{API_BASE_URL}/index", json={
                "image_data": item["image_data"],
                "image_id": item["image_id"],
                "metadata": item.get("metadata", {})
            })
            
            if response.status_code == 200:
                results.append({
                    "status": "success",
                    "image_id": item["image_id"],
                    "message": "Image processed successfully"
                })
            else:
                results.append({
                    "status": "error",
                    "image_id": item["image_id"],
                    "message": f"API error: {response.status_code}"
                })
        
        successful = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "error")
        
        return {
            "status": "completed",
            "total": total_images,
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
