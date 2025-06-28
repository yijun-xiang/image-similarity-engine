#!/usr/bin/env python3

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_service import get_vector_service
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    settings = get_settings()
    logger.info(f"Initializing vector database: {settings.qdrant_collection_name}")
    
    try:
        vector_service = get_vector_service()
        await vector_service.connect()
        
        info = await vector_service.get_collection_info()
        logger.info(f"Collection info: {info}")
        
        logger.info("Database initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())
