# Image Similarity Engine - Backend

High-performance ML backend service for scalable image similarity search, capable of handling million-scale image datasets.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI   │────▶│     CLIP     │────▶│   Qdrant    │
│   Gateway   │     │   Encoder    │     │  Vector DB  │
└─────────────┘     └──────────────┘     └─────────────┘
       │                                         ▲
       │            ┌──────────────┐            │
       └───────────▶│    Redis     │────────────┘
                    │    Cache     │
                    └──────────────┘
```

## 🚀 Tech Stack

- **Framework**: FastAPI (Python 3.12)
- **ML Model**: CLIP ViT-B/32 (OpenAI)
- **Vector Database**: Qdrant
- **Cache Layer**: Redis
- **ML Framework**: PyTorch 2.7 with MPS/CUDA support
- **Process Manager**: Uvicorn + Gunicorn
- **Containerization**: Docker + Docker Compose

## 📊 Performance Metrics

- **Throughput**: 94+ requests/second
- **Latency**: 105ms average (476ms P95)
- **Model Loading**: < 2 seconds
- **Feature Extraction**: ~30ms per image
- **Vector Search**: < 50ms for 1M vectors
- **Cache Hit Rate**: > 75%

## 🛠️ API Endpoints

### Image Search
```http
POST /api/v1/search
Content-Type: application/json

{
  "image_data": "base64_encoded_image",
  "top_k": 10,
  "threshold": 0.7,
  "include_metadata": true
}
```

### Image Indexing
```http
POST /api/v1/index
Content-Type: application/json

{
  "image_data": "base64_encoded_image",
  "image_id": "unique_identifier",
  "metadata": {
    "tags": ["nature", "landscape"],
    "source": "user_upload"
  }
}
```

### Health Check
```http
GET /api/v1/health
```

### System Statistics
```http
GET /api/v1/stats
```

## 🔧 Installation

### Prerequisites
- Python 3.12+
- Poetry
- Docker & Docker Compose
- 4GB+ RAM
- GPU (optional, for acceleration)

### Quick Start

1. **Clone and setup**
```bash
cd backend
poetry install
```

2. **Start dependencies**
```bash
docker-compose up -d
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Run the server**
```bash
poetry run uvicorn app.main:app --reload
```

## 🏃 Development

### Project Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/      # API routes
│   │   └── dependencies.py # Shared dependencies
│   ├── core/
│   │   ├── config.py       # Settings
│   │   └── security.py     # Auth (if needed)
│   ├── models/
│   │   └── schemas.py      # Pydantic models
│   ├── services/
│   │   ├── ml_service.py   # CLIP integration
│   │   ├── vector_service.py # Qdrant operations
│   │   └── cache_service.py  # Redis caching
│   └── main.py             # Application entry
├── tests/                  # Test suite
├── scripts/               # Utility scripts
└── pyproject.toml         # Dependencies
```

### Key Services

#### ML Service
- CLIP model management
- Batch processing support
- GPU/MPS acceleration
- Model caching

#### Vector Service
- Qdrant collection management
- Efficient similarity search
- Metadata filtering
- Index optimization

#### Cache Service
- Redis integration
- TTL management
- Cache invalidation
- Performance monitoring

## 🧪 Testing

```bash
# Run unit tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run integration tests
poetry run pytest tests/integration/

# Load testing
poetry run locust -f tests/load/locustfile.py
```

## 📈 Performance Optimization

### 1. Model Optimization
- Model loaded once at startup
- Batch processing for multiple images
- MPS acceleration on Apple Silicon
- CUDA support for NVIDIA GPUs

### 2. Caching Strategy
- Feature vectors cached in Redis
- Search results cached with TTL
- Automatic cache warming
- LRU eviction policy

### 3. Database Optimization
- HNSW index for fast search
- Optimized vector dimensions (512)
- Payload indexing for metadata
- Asynchronous operations

### 4. API Optimization
- Connection pooling
- Request/response compression
- Async request handling
- Rate limiting

## 🚢 Deployment

### Docker
```bash
docker build -t image-similarity-backend .
docker run -p 8000:8000 image-similarity-backend
```

### Docker Compose
```bash
docker-compose up --build
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: similarity-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: similarity-backend
  template:
    metadata:
      labels:
        app: similarity-backend
    spec:
      containers:
      - name: backend
        image: image-similarity-backend:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

## 🔍 Monitoring

- **Metrics**: Prometheus + Grafana
- **Logging**: Structured logging with JSON
- **Tracing**: OpenTelemetry support
- **Health Checks**: Liveness and readiness probes

## 🔐 Security

- Input validation with Pydantic
- Rate limiting per IP
- CORS configuration
- API key authentication (optional)
- Image size limits

## 🤝 Contributing

1. Use Poetry for dependency management
2. Follow PEP 8 style guide
3. Add type hints for all functions
4. Write tests for new features
5. Update API documentation

## 📄 License

MIT License - Part of the Image Similarity Engine project