#!/usr/bin/env python3

import asyncio
import httpx
import base64
from PIL import Image, ImageDraw
import io
import random
import time
import logging
from typing import List
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDataGenerator:
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
        self.categories = [
            "landscape", "portrait", "abstract", "nature", 
            "urban", "technology", "art", "sports", "food", "animals"
        ]
    
    def generate_synthetic_image(self, category: str, index: int) -> str:
        img = Image.new('RGB', (224, 224))
        draw = ImageDraw.Draw(img)
        
        color_map = {
            "landscape": [(34, 139, 34), (135, 206, 235)],
            "portrait": [(255, 218, 185), (255, 192, 203)],
            "abstract": [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(2)],
            "nature": [(0, 128, 0), (139, 69, 19)],
            "urban": [(128, 128, 128), (192, 192, 192)],
            "technology": [(0, 0, 255), (255, 255, 255)],
            "art": [(255, 0, 0), (255, 255, 0)],
            "sports": [(255, 140, 0), (255, 255, 255)],
            "food": [(255, 69, 0), (255, 215, 0)],
            "animals": [(139, 90, 43), (255, 255, 255)]
        }
        
        colors = color_map.get(category, [(255, 255, 255), (0, 0, 0)])
        
        for y in range(224):
            ratio = y / 224
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.rectangle([(0, y), (224, y + 1)], fill=(r, g, b))
        
        for _ in range(5):
            shape_type = random.choice(['circle', 'rectangle'])
            x1 = random.randint(0, 180)
            y1 = random.randint(0, 180)
            x2 = x1 + random.randint(20, 40)
            y2 = y1 + random.randint(20, 40)
            
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            
            if shape_type == 'circle':
                draw.ellipse([x1, y1, x2, y2], fill=color)
            else:
                draw.rectangle([x1, y1, x2, y2], fill=color)
        
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def index_batch(self, images_data: List[dict], batch_size: int = 100):
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(0, len(images_data), batch_size):
                batch = images_data[i:i + batch_size]
                
                tasks = []
                for img_data in batch:
                    task = client.post(
                        f"{self.api_url}/api/v1/index",
                        json=img_data
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
                logger.info(f"Batch {i//batch_size + 1}: {success_count}/{len(batch)} indexed successfully")
    
    async def generate_and_index(self, total_images: int = 10000):
        logger.info(f"Starting to generate and index {total_images} images...")
        start_time = time.time()
        
        images_data = []
        
        for i in range(total_images):
            category = self.categories[i % len(self.categories)]
            image_data = self.generate_synthetic_image(category, i)
            
            images_data.append({
                "image_data": image_data,
                "image_id": f"test_image_{i:06d}",
                "metadata": {
                    "category": category,
                    "index": i,
                    "timestamp": time.time(),
                    "synthetic": True
                }
            })
            
            if (i + 1) % 1000 == 0:
                logger.info(f"Generated {i + 1}/{total_images} images")
        
        logger.info("Starting batch indexing...")
        await self.index_batch(images_data)
        
        total_time = time.time() - start_time
        logger.info(f"Completed in {total_time:.2f} seconds")
        logger.info(f"Average: {total_images / total_time:.2f} images/second")
    
    async def verify_data(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}/api/v1/stats")
            if response.status_code == 200:
                stats = response.json()
                logger.info(f"Current stats: {stats}")
            
            test_image = self.generate_synthetic_image("landscape", 999)
            response = await client.post(
                f"{self.api_url}/api/v1/search",
                json={
                    "image_data": test_image,
                    "top_k": 10
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                logger.info(f"Search test: Found {results['total_found']} similar images")
                logger.info(f"Search time: {results['search_time_ms']:.0f}ms")


async def main():
    generator = TestDataGenerator()
    
    logger.info("=== Phase 1: Testing with 100 images ===")
    await generator.generate_and_index(100)
    await generator.verify_data()
    
    print("\nDo you want to generate 10,000 images? (y/n): ", end='')
    if input().lower() == 'y':
        logger.info("\n=== Phase 2: Generating 10,000 images ===")
        await generator.generate_and_index(10000)
        await generator.verify_data()


if __name__ == "__main__":
    asyncio.run(main())
