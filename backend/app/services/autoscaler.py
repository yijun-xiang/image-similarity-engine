import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScalingPolicy:
    min_instances: int
    max_instances: int
    target_cpu_percent: float
    target_memory_percent: float
    target_queue_length: int
    scale_up_threshold: float
    scale_down_threshold: float
    cooldown_seconds: int


class AutoScaler:
    def __init__(self, policy: ScalingPolicy):
        self.policy = policy
        self.current_instances = policy.min_instances
        self.last_scale_time = datetime.now()
        self.metrics_history = []
        self._monitoring_task = None
    
    async def start(self):
        self._monitoring_task = asyncio.create_task(self._monitor_and_scale())
        logger.info("AutoScaler started")
    
    async def stop(self):
        if self._monitoring_task:
            self._monitoring_task.cancel()
    
    async def _monitor_and_scale(self):
        while True:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append({
                    'timestamp': datetime.now(),
                    'metrics': metrics
                })
                
                if len(self.metrics_history) > 100:
                    self.metrics_history.pop(0)
                
                scaling_decision = self._make_scaling_decision(metrics)
                
                if scaling_decision != 0:
                    await self._scale(scaling_decision)
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"AutoScaler error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _collect_metrics(self) -> Dict[str, float]:
        from app.services.performance_monitor import get_performance_monitor
        
        monitor = await get_performance_monitor()
        system_health = monitor.get_system_health()
        
        return {
            'cpu_percent': system_health['metrics']['cpu'].get('mean', 0),
            'memory_percent': system_health['metrics']['memory'].get('mean', 0),
            'queue_length': await self._get_queue_length(),
            'response_time_p95': await self._get_response_time_p95()
        }
    
    async def _get_queue_length(self) -> int:
        return 0
    
    async def _get_response_time_p95(self) -> float:
        return 100.0
    
    def _make_scaling_decision(self, metrics: Dict[str, float]) -> int:
        if not self._can_scale():
            return 0
        
        cpu_load = metrics['cpu_percent'] / self.policy.target_cpu_percent
        memory_load = metrics['memory_percent'] / self.policy.target_memory_percent
        queue_load = metrics['queue_length'] / max(self.policy.target_queue_length, 1)
        
        max_load = max(cpu_load, memory_load, queue_load)
        
        if max_load > self.policy.scale_up_threshold:
            desired_instances = min(
                int(self.current_instances * max_load),
                self.policy.max_instances
            )
            return max(1, desired_instances - self.current_instances)
        
        elif max_load < self.policy.scale_down_threshold:
            desired_instances = max(
                int(self.current_instances * max_load),
                self.policy.min_instances
            )
            return min(-1, desired_instances - self.current_instances)
        
        return 0
    
    def _can_scale(self) -> bool:
        cooldown = timedelta(seconds=self.policy.cooldown_seconds)
        return datetime.now() - self.last_scale_time > cooldown
    
    async def _scale(self, delta: int):
        if delta > 0:
            logger.info(f"Scaling up by {delta} instances")
            await self._scale_up(delta)
        else:
            logger.info(f"Scaling down by {abs(delta)} instances")
            await self._scale_down(abs(delta))
        
        self.current_instances += delta
        self.last_scale_time = datetime.now()
    
    async def _scale_up(self, count: int):
        pass
    
    async def _scale_down(self, count: int):
        pass
    
    def get_status(self) -> Dict[str, Any]:
        recent_metrics = {}
        if self.metrics_history:
            recent = self.metrics_history[-1]['metrics']
            recent_metrics = recent
        
        return {
            'current_instances': self.current_instances,
            'min_instances': self.policy.min_instances,
            'max_instances': self.policy.max_instances,
            'last_scale_time': self.last_scale_time.isoformat(),
            'can_scale': self._can_scale(),
            'recent_metrics': recent_metrics,
            'metrics_history_count': len(self.metrics_history)
        }
