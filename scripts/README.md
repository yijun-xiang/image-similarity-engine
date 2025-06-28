# Scripts Directory Structure

## /scripts (Root Directory)
System-level Shell scripts for infrastructure management:

- **start.sh** - Start basic development environment
- **start_million_scale.sh** - Start full million-scale infrastructure  
- **start_million_scale_simple.sh** - Start simplified million-scale setup
- **start-monitoring.sh** - Start Prometheus/Grafana monitoring stack
- **test-monitoring.sh** - Test monitoring services health
- **test.sh** - Run all tests (unit, integration, benchmark)
- **build-and-push.sh** - Build Docker images and push to registry
- **deploy-k8s.sh** - Deploy to Kubernetes cluster

## /backend/scripts
Python scripts for application-specific tasks:

- **benchmark.py** - Performance benchmarking tool
- **download_models.py** - Download CLIP models from HuggingFace
- **init_database.py** - Initialize Qdrant vector database
- **load_test_million.py** - Million-scale load testing
- **test_scale.py** - Test scaled deployment

## Usage Examples

```bash
# Start development environment
bash scripts/start.sh

# Start million-scale environment
bash scripts/start_million_scale_simple.sh

# Run benchmarks (from backend directory)
cd backend && poetry run python scripts/benchmark.py

# Run load test (from backend directory)
cd backend && poetry run python scripts/load_test_million.py
```

## Script Details

### Infrastructure Scripts (/scripts)

#### start.sh
Starts the basic development environment with:
- Docker services (Qdrant, Redis, RabbitMQ)
- Downloads ML models
- Initializes database
- Runs health checks

#### start_million_scale_simple.sh  
Starts simplified million-scale setup with:
- 3 Qdrant shards
- 3 Backend instances
- 1 Redis cluster
- HAProxy load balancer

#### start-monitoring.sh
Starts monitoring stack:
- Prometheus (metrics collection)
- Grafana (visualization)
- AlertManager (alerting)
- Node Exporter (system metrics)

### Application Scripts (/backend/scripts)

#### benchmark.py
Performance testing tool that measures:
- Request throughput (req/s)
- Latency percentiles (P50, P95, P99)
- Success rates
- Concurrent request handling

#### load_test_million.py
Million-scale load testing with:
- Configurable client count (default: 100)
- Mixed workload (index + search)
- Detailed performance metrics
- Error tracking

#### test_scale.py
Simple scale testing that:
- Verifies all backends are healthy
- Tests index operation
- Tests search via load balancer
- Reports basic metrics