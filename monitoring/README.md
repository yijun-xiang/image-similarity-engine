# Monitoring Stack

Real-time performance monitoring for the Image Similarity Engine using Prometheus, Grafana, and AlertManager.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Backend API   │────▶│  Prometheus  │────▶│   Grafana   │
│  (metrics:8000) │     │    (9090)    │     │   (3001)    │
└─────────────────┘     └──────────────┘     └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ AlertManager │
                        │    (9093)    │
                        └──────────────┘
```

## Quick Start

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3001 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| AlertManager | http://localhost:9093 | - |
| Backend Metrics | http://localhost:8000/metrics | - |

## Metrics Tracked

### API Metrics
- `http_requests_total` - Total requests by endpoint/status
- `http_request_duration_seconds` - Request latency (P50/P95/P99)
- `active_requests` - Currently processing requests

### ML Metrics
- `ml_inference_duration_seconds` - Model inference time
- `ml_inference_total` - Total inferences by operation
- `indexed_images_total` - Images in database

### Search Metrics
- `vector_search_duration_seconds` - Vector DB query time
- `vector_search_results_count` - Results per search

### Cache Metrics
- `cache_hits_total` / `cache_misses_total` - Cache effectiveness
- `cache_operation_duration_seconds` - Cache latency

## Grafana Dashboard

The main dashboard includes:
- Request rate and latency graphs
- Cache hit rate gauge (currently 85.7%)
- Total indexed images counter
- ML inference performance
- Service health status
- Error tracking by type

## Alerts

Pre-configured alerts for:
- High request latency (> 500ms P95)
- High error rate (> 10%)
- Low cache hit rate (< 50%)
- Service downtime
- High memory usage (> 90%)

## Testing

Generate test traffic:
```bash
bash scripts/test-monitoring.sh
```

Check metrics manually:
```bash
curl http://localhost:8000/metrics | grep http_requests_total
```

## Troubleshooting

### No data in Grafana
1. Check Prometheus targets: http://localhost:9090/targets
2. Ensure backend is running: `curl http://localhost:8000/health`
3. Generate traffic: `cd backend && poetry run python ../demo.py`

### Container issues
```bash
docker-compose -f docker-compose.monitoring.yml logs prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

## Configuration Files

- `prometheus/prometheus.yml` - Scrape configs and targets
- `grafana/dashboards/` - Dashboard JSON files
- `grafana/datasources/` - Prometheus datasource
- `alertmanager/alertmanager.yml` - Alert routing