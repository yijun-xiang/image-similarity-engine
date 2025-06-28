#!/usr/bin/env python3

import asyncio
import base64
import time
import statistics
import logging
from typing import List
import httpx
from PIL import Image
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BenchmarkTester:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def generate_test_image(self, size: tuple = (224, 224)) -> str:
        image = Image.new('RGB', size, color='red')
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def test_single_search(self, image_data: str) -> float:
        start_time = time.time()
        
        response = await self.client.post(
            f"{self.api_url}/api/v1/search",
            json={
                "image_data": image_data,
                "top_k": 10,
                "threshold": 0.0
            }
        )
        
        if response.status_code == 200:
            return time.time() - start_time
        else:
            raise Exception(f"Request failed: {response.status_code}")
    
    async def test_concurrent_search(self, num_requests: int = 50, concurrency: int = 10):
        logger.info(f"Starting concurrent test: {num_requests} requests, {concurrency} concurrent")
        
        image_data = self.generate_test_image()
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_test():
            async with semaphore:
                return await self.test_single_search(image_data)
        
        start_time = time.time()
        
        tasks = [limited_test() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        successful_times = [
            result for result in results 
            if isinstance(result, float)
        ]
        
        failed_count = len(results) - len(successful_times)
        
        if successful_times:
            avg_latency = statistics.mean(successful_times)
            p95_latency = statistics.quantiles(successful_times, n=20)[18]
            throughput = len(successful_times) / total_time
            
            logger.info("=== Benchmark Results ===")
            logger.info(f"Total Requests: {num_requests}")
            logger.info(f"Successful: {len(successful_times)}")
            logger.info(f"Failed: {failed_count}")
            logger.info(f"Success Rate: {len(successful_times)/num_requests*100:.1f}%")
            logger.info(f"Total Time: {total_time:.2f}s")
            logger.info(f"Throughput: {throughput:.2f} req/s")
            logger.info(f"Average Latency: {avg_latency:.3f}s")
            logger.info(f"95th Percentile Latency: {p95_latency:.3f}s")
            
            return {
                "total_requests": num_requests,
                "successful_requests": len(successful_times),
                "failed_requests": failed_count,
                "success_rate": len(successful_times) / num_requests,
                "total_time": total_time,
                "throughput": throughput,
                "avg_latency": avg_latency,
                "p95_latency": p95_latency
            }
        else:
            logger.error("All requests failed!")
            return None
    
    async def test_health_check(self):
        logger.info("Testing health check endpoint...")
        
        response = await self.client.get(f"{self.api_url}/api/v1/health")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Health check passed: {data['status']}")
            logger.info(f"Services: {data['services']}")
            return True
        else:
            logger.error(f"Health check failed: {response.status_code}")
            return False
    
    async def close(self):
        await self.client.aclose()

async def main():
    tester = BenchmarkTester()
    
    try:
        if not await tester.test_health_check():
            logger.error("Service is not healthy, aborting benchmark")
            return
        
        await tester.test_concurrent_search(num_requests=50, concurrency=10)
        
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
