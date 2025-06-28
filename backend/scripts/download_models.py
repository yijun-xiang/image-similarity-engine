#!/usr/bin/env python3

import os
import logging
from transformers import CLIPProcessor, CLIPModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_models():
    model_name = "openai/clip-vit-base-patch32"
    cache_dir = "./models"
    
    logger.info(f"Downloading model: {model_name}")
    logger.info(f"Cache directory: {cache_dir}")
    
    try:
        processor = CLIPProcessor.from_pretrained(
            model_name,
            cache_dir=cache_dir
        )
        logger.info("Processor downloaded successfully")
        
        model = CLIPModel.from_pretrained(
            model_name,
            cache_dir=cache_dir
        )
        logger.info("Model downloaded successfully")
        
        logger.info("All models downloaded and cached successfully!")
        
    except Exception as e:
        logger.error(f"Failed to download models: {str(e)}")
        raise

if __name__ == "__main__":
    download_models()
