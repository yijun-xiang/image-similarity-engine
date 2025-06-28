#!/usr/bin/env python3

import asyncio
import httpx
import base64
from PIL import Image
import io
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_single_request():
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    image_data = base64.b64encode(buffer.getvalue()).decode()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8080/api/v1/index",
                json={
                    "image_data": image_data,
                    "image_id": f"test_{time.time()}",
                    "metadata": {"test": True}
                },
                timeout=30.0
            )
            logger.info(f"Index response: {response.status_code}")
            
            response = await client.post(
                "http://localhost:8080/api/v1/search",
                json={
                    "image_data": image_data,
                    "top_k": 5
                },
                timeout=30.0
            )
            logger.info(f"Search response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {data['total_found']} results")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")


async def simple_load_test(duration_seconds: int = 30):
    logger.info(f"Running simple load test for {duration_seconds} seconds")
    
    start_time = time.time()
    request_count = 0
    error_count = 0
    
    while time.time() - start_time < duration_seconds:
        try:
            await test_single_request()
            request_count += 2
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            error_count += 1
        
        await asyncio.sleep(0.5)
    
    total_time = time.time() - start_time
    logger.info(f"\n=== Results ===")
    logger.info(f"Duration: {total_time:.2f}s")
    logger.info(f"Total requests: {request_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Throughput: {request_count/total_time:.2f} req/s")


if __name__ == "__main__":
    asyncio.run(simple_load_test(30))
