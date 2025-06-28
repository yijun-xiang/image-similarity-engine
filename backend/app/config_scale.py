from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings


class ScaleSettings(BaseSettings):
    shard_count: int = 8
    shard_replicas: int = 2
    
    cache_strategy: str = "multi_tier"
    local_cache_size: int = 50000
    redis_cache_size_gb: int = 32
    cache_ttl_short: int = 300
    cache_ttl_medium: int = 3600
    cache_ttl_long: int = 86400
    
    batch_size_index: int = 1000
    batch_size_search: int = 100
    batch_timeout: float = 5.0
    
    connection_pool_size: int = 50
    redis_pool_size: int = 100
    grpc_pool_size: int = 20
    
    query_optimization: bool = True
    use_quantization: bool = True
    use_gpu_acceleration: bool = True
    
    prefetch_enabled: bool = True
    prefetch_size: int = 1000
    
    monitoring_enabled: bool = True
    metrics_port: int = 9090
    
    index_segments: int = 16
    max_vectors_per_segment: int = 100000
    
    replication_factor: int = 2
    consistency_level: str = "eventual"
    
    load_balancer_algorithm: str = "round_robin"
    circuit_breaker_threshold: int = 50
    circuit_breaker_timeout: int = 60
    
    compression_enabled: bool = True
    compression_level: int = 6
    
    class Config:
        env_file = ".env.scale"
        case_sensitive = False


@lru_cache()
def get_scale_settings() -> ScaleSettings:
    return ScaleSettings()
