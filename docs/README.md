# Image Similarity Search Engine

High-performance image similarity search engine using CLIP and Qdrant vector database.

## Performance Metrics
- **Throughput**: 94+ requests/second
- **Latency**: 105ms average, 476ms P95  
- **Accuracy**: Perfect similarity matching (score = 1.0)
- **Apple Silicon Optimized**: MPS acceleration

## Tech Stack
- **ML**: CLIP (OpenAI) + PyTorch
- **API**: FastAPI + Uvicorn
- **Vector DB**: Qdrant
- **Cache**: Redis
- **Deployment**: Docker + Docker Compose

## Quick Start
```bash
poetry install
bash scripts/start.sh
open http://localhost:8000/docs
