from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator
import time
from functools import wraps
from typing import Callable

app_info = Info('app_info', 'Application information')
app_info.info({
    'version': '1.0.0',
    'name': 'image-similarity-engine',
    'framework': 'fastapi'
})

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ml_inference_duration_seconds = Histogram(
    'ml_inference_duration_seconds',
    'ML model inference duration',
    ['model_name', 'operation']
)

ml_inference_total = Counter(
    'ml_inference_total',
    'Total ML inferences',
    ['model_name', 'operation', 'status']
)

vector_search_duration_seconds = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration'
)

vector_search_results = Histogram(
    'vector_search_results_count',
    'Number of results returned by vector search'
)

indexed_images_total = Gauge(
    'indexed_images_total',
    'Total number of indexed images'
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration',
    ['operation']
)

active_requests = Gauge(
    'active_requests',
    'Number of active requests'
)

errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

def track_ml_inference(model_name: str, operation: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                ml_inference_duration_seconds.labels(
                    model_name=model_name,
                    operation=operation
                ).observe(duration)
                ml_inference_total.labels(
                    model_name=model_name,
                    operation=operation,
                    status=status
                ).inc()
        return wrapper
    return decorator

def track_vector_search():
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                results = await func(*args, **kwargs)
                duration = time.time() - start_time
                vector_search_duration_seconds.observe(duration)
                vector_search_results.observe(len(results))
                return results
            except Exception as e:
                raise e
        return wrapper
    return decorator

def track_cache_operation(operation: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                cache_operation_duration_seconds.labels(
                    operation=operation
                ).observe(duration)
                return result
            except Exception as e:
                raise e
        return wrapper
    return decorator
EOF