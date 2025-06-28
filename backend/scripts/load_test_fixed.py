#!/usr/bin/env python3

import asyncio
import httpx
import time
import random
import base64
from PIL import Image
import io
import logging
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadTester:
    def __init__(self, api_url: str = "http://localhost:8080", num_clients: int = 10):
        self.api_url = api_url
        self.num_clients = num_clients
        self.results = []
        self.errors = []
    
    def generate_random_image(self) -> str:
        color = tuple(random.randint(0, 255) for _ in range(3))
        image = Image.new('RGB', (224, 224), color=color)
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
                    "metadata": {"test": "load_test", "timestamp": time.time()}
                }
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
                    "top_k": 10,
                    "threshold": 0.0
                }
            )
            
            if response.status_code == 200:
                return time.time() - start_time
            else:
                self.errors.append(f"Search error: {response.status_code}")
                return -1
                
        except Exception as e:
            self.errors.append(f"Search exception: {str(e)}")
            return -1
    
    async def client_worker(self, client_id: int, duration_seconds: int):
        async with httpx.AsyncClient(timeout=30.0) as client:
            start_time = time.time()
            
            while time.time() - start_time < duration_seconds:
                operation = random.choice(['index', 'search'])
                image_data = self.generate_random_image()
                
                if operation == 'index':
                    image_id = f"client_{client_id}_img_{int(time.time()*1000)}"
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
    
    async def run_load_test(self, duration_seconds: int = 60):
        logger.info(f"Starting load test with {self.num_clients} clients for {duration_seconds} seconds")
        
        tasks = []
        for client_id in range(self.num_clients):
            task = asyncio.create_task(self.client_worker(client_id, duration_seconds))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        self.print_results()
    
    def print_results(self):
        if not self.results:
            logger.error("No successful operations")
            if self.errors:
                logger.error(f"Errors: {self.errors[:5]}")
            return
        
        index_times = [r['duration'] for r in self.results if r['operation'] == 'index']
        search_times = [r['duration'] for r in self.results if r['operation'] == 'search']
        
        logger.info("\n=== LOAD TEST RESULTS ===")
        logger.info(f"Total Operations: {len(self.results)}")
        logger.info(f"Total Errors: {len(self.errors)}")
        
        if index_times:
            logger.info("\n--- INDEX OPERATIONS ---")
            logger.info(f"Count: {len(index_times)}")
            logger.info(f"Mean: {statistics.mean(index_times):.3f}s")
            logger.info(f"P50: {statistics.median(index_times):.3f}s")
        
        if search_times:
            logger.info("\n--- SEARCH OPERATIONS ---")
            logger.info(f"Count: {len(search_times)}")
            logger.info(f"Mean: {statistics.mean(search_times):.3f}s")
            logger.info(f"P50: {statistics.median(search_times):.3f}s")


async def main():
    tester = LoadTester(num_clients=10)
    await tester.run_load_test(duration_seconds=30)


if __name__ == "__main__":
    asyncio.run(main())
