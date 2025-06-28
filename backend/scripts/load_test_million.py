#!/usr/bin/env python3

import asyncio
import httpx
import time
import random
import base64
from PIL import Image
import io
import numpy as np
from typing import List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MillionScaleLoadTester:
    def __init__(self, api_url: str = "http://localhost:8000", num_clients: int = 100):
        self.api_url = api_url
        self.num_clients = num_clients
        self.results = []
        self.errors = []
    
    def generate_random_image(self, size: tuple = (224, 224)) -> str:
        color = tuple(random.randint(0, 255) for _ in range(3))
        image = Image.new('RGB', size, color=color)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def index_image(self, client: httpx.AsyncClient, image_data: str, image_id: str) -> float:
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{self.api_url}/api/v1/index",
                json={
                    "image_data": image_data,
                    "image_id": image_id,
                    "metadata": {
                        "batch": "million_scale_test",
                        "timestamp": time.time()
                    }
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return time.time() - start_time
            else:
                self.errors.append(f"Index error: {response.status_code}")
                return -1
                
        except Exception as e:
            self.errors.append(f"Index exception: {str(e)}")
            return -1
    
    async def search_image(self, client: httpx.AsyncClient, image_data: str) -> float:
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{self.api_url}/api/v1/search",
                json={
                    "image_data": image_data,
                    "top_k": 100,
                    "threshold": 0.0
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return time.time() - start_time
            else:
                self.errors.append(f"Search error: {response.status_code}")
                return -1
                
        except Exception as e:
            self.errors.append(f"Search exception: {str(e)}")
            return -1
    
    async def run_client_workload(self, client_id: int, num_operations: int):
        async with httpx.AsyncClient() as client:
            for i in range(num_operations):
                operation = random.choice(['index', 'search'])
                image_data = self.generate_random_image()
                
                if operation == 'index':
                    image_id = f"client_{client_id}_image_{i}"
                    duration = await self.index_image(client, image_data, image_id)
                else:
                    duration = await self.search_image(client, image_data)
                
                if duration > 0:
                    self.results.append({
                        'client_id': client_id,
                        'operation': operation,
                        'duration': duration,
                        'timestamp': time.time()
                    })
                
                await asyncio.sleep(random.uniform(0.1, 0.5))
    
    async def run_load_test(self, duration_seconds: int = 300):
        logger.info(f"Starting load test with {self.num_clients} clients for {duration_seconds} seconds")
        
        start_time = time.time()
        operations_per_client = int(duration_seconds * 2)
        
        tasks = []
        for client_id in range(self.num_clients):
            task = asyncio.create_task(
                self.run_client_workload(client_id, operations_per_client)
            )
            tasks.append(task)
            await asyncio.sleep(0.01)
        
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        self.print_results(total_time)
    
    def print_results(self, total_time: float):
        if not self.results:
            logger.error("No successful operations")
            return
        
        index_times = [r['duration'] for r in self.results if r['operation'] == 'index']
        search_times = [r['duration'] for r in self.results if r['operation'] == 'search']
        
        logger.info("\n=== MILLION SCALE LOAD TEST RESULTS ===")
        logger.info(f"Total Duration: {total_time:.2f} seconds")
        logger.info(f"Total Operations: {len(self.results)}")
        logger.info(f"Total Errors: {len(self.errors)}")
        logger.info(f"Success Rate: {len(self.results) / (len(self.results) + len(self.errors)) * 100:.2f}%")
        
        if index_times:
            logger.info("\n--- INDEX OPERATIONS ---")
            logger.info(f"Count: {len(index_times)}")
            logger.info(f"Mean: {statistics.mean(index_times):.3f}s")
            logger.info(f"P50: {statistics.median(index_times):.3f}s")
            logger.info(f"P95: {statistics.quantiles(index_times, n=20)[18]:.3f}s")
            logger.info(f"P99: {statistics.quantiles(index_times, n=100)[98]:.3f}s")
            logger.info(f"Throughput: {len(index_times) / total_time:.2f} ops/sec")
        
        if search_times:
            logger.info("\n--- SEARCH OPERATIONS ---")
            logger.info(f"Count: {len(search_times)}")
            logger.info(f"Mean: {statistics.mean(search_times):.3f}s")
            logger.info(f"P50: {statistics.median(search_times):.3f}s")
            logger.info(f"P95: {statistics.quantiles(search_times, n=20)[18]:.3f}s")
            logger.info(f"P99: {statistics.quantiles(search_times, n=100)[98]:.3f}s")
            logger.info(f"Throughput: {len(search_times) / total_time:.2f} ops/sec")
        
        logger.info(f"\nTotal Throughput: {len(self.results) / total_time:.2f} ops/sec")


async def main():
    tester = MillionScaleLoadTester(num_clients=100)
    await tester.run_load_test(duration_seconds=300)


if __name__ == "__main__":
    asyncio.run(main())
