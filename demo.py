import requests
import base64
from PIL import Image
import io
import time


class ImageSimilarityDemo:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        
    def create_test_image(self, color, size=(100, 100)):
        img = Image.new('RGB', size, color=color)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    def index_image(self, image_data, image_id, metadata):
        response = requests.post(f"{self.api_url}/api/v1/index", json={
            'image_data': image_data,
            'image_id': image_id,
            'metadata': metadata
        })
        return response.json()
    
    def search_similar(self, image_data, top_k=5):
        response = requests.post(f"{self.api_url}/api/v1/search", json={
            'image_data': image_data,
            'top_k': top_k,
            'threshold': 0.0
        })
        return response.json()
    
    def run_demo(self):
        print("=== Image Similarity Search Engine Demo ===")
        
        colors = ['purple', 'orange', 'pink']
        
        print("\n1. Indexing new test images...")
        for color in colors:
            image_data = self.create_test_image(color)
            result = self.index_image(image_data, f"demo_{color}", {"color": color, "demo": True})
            print(f"Indexed {color} image: {result['processing_time_ms']:.1f}ms")
        
        print("\n2. Testing similarity search...")
        query_image = self.create_test_image('blue')
        start_time = time.time()
        results = self.search_similar(query_image)
        search_time = (time.time() - start_time) * 1000
        
        print(f"Search completed in {search_time:.1f}ms")
        print(f"Found {len(results['results'])} similar images:")
        
        for result in results['results']:
            print(f"  - {result['image_id']}: score={result['score']:.3f}")
        
        print(f"\nQuery ID: {results['query_id']}")
        print(f"Total processing time: {results['search_time_ms']:.1f}ms")


if __name__ == "__main__":
    demo = ImageSimilarityDemo()
    demo.run_demo()
