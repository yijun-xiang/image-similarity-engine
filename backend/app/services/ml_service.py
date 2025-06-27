import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import io
import base64
import logging
import asyncio
from typing import Union, List, Optional
from functools import lru_cache

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MLService:
    def __init__(self):
        self.model: Optional[CLIPModel] = None
        self.processor: Optional[CLIPProcessor] = None
        self.device = self._get_device()
        logger.info(f"ML Service initialized with device: {self.device}")
    
    def _get_device(self) -> str:
        if settings.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return settings.device
    
    async def load_model(self):
        if self.model is not None:
            return
        
        logger.info(f"Loading model: {settings.model_name}")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model_sync)
        
        logger.info("Model loaded successfully")
    
    def _load_model_sync(self):
        self.processor = CLIPProcessor.from_pretrained(
            settings.model_name,
            cache_dir=settings.model_cache_dir
        )
        self.model = CLIPModel.from_pretrained(
            settings.model_name,
            cache_dir=settings.model_cache_dir
        ).to(self.device)
        self.model.eval()
    
    def _decode_image(self, image_data: str) -> Image.Image:
        try:
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
        except Exception as e:
            logger.error(f"Failed to decode image: {str(e)}")
            raise ValueError(f"Invalid image data: {str(e)}")
    
    def _validate_image_size(self, image_bytes: bytes):
        if len(image_bytes) > settings.max_image_size:
            raise ValueError(f"Image size {len(image_bytes)} exceeds maximum {settings.max_image_size}")
    
    async def extract_features(self, image_data: str) -> np.ndarray:
        if self.model is None:
            await self.load_model()
        
        try:
            image = self._decode_image(image_data)
            
            loop = asyncio.get_event_loop()
            features = await loop.run_in_executor(
                None, self._extract_features_sync, image
            )
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            raise
    
    def _extract_features_sync(self, image: Image.Image) -> np.ndarray:
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy().flatten()
    
    async def batch_extract_features(self, images_data: List[str]) -> List[np.ndarray]:
        if self.model is None:
            await self.load_model()
        
        try:
            images = [self._decode_image(img_data) for img_data in images_data]
            
            batch_size = settings.batch_size
            all_features = []
            
            for i in range(0, len(images), batch_size):
                batch_images = images[i:i + batch_size]
                
                loop = asyncio.get_event_loop()
                batch_features = await loop.run_in_executor(
                    None, self._batch_extract_features_sync, batch_images
                )
                all_features.extend(batch_features)
            
            return all_features
            
        except Exception as e:
            logger.error(f"Batch feature extraction failed: {str(e)}")
            raise
    
    def _batch_extract_features_sync(self, images: List[Image.Image]) -> List[np.ndarray]:
        inputs = self.processor(images=images, return_tensors="pt", padding=True).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return [feat.cpu().numpy() for feat in image_features]
    
    def get_feature_dimension(self) -> int:
        if self.model is None:
            return 512
        return self.model.config.projection_dim


@lru_cache()
def get_ml_service() -> MLService:
    return MLService()
