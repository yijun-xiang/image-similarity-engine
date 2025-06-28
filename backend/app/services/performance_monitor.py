import asyncio
import time
from typing import Dict, Any, List, Optional
from collections import deque, defaultdict
from datetime import datetime, timedelta
import psutil
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    def __init__(self, window_size: int = 300):
        self.window_size = window_size
        self.metrics = defaultdict(lambda: deque(maxlen=window_size))
        self.start_time = time.time()
        self._monitoring_task = None
    
    async def start(self):
        self._monitoring_task = asyncio.create_task(self._monitor_system())
        logger.info("Performance monitoring started")
    
    async def stop(self):
        if self._monitoring_task:
            self._monitoring_task.cancel()
    
    async def _monitor_system(self):
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                self.record_metric('system.cpu_percent', cpu_percent)
                self.record_metric('system.memory_percent', memory.percent)
                self.record_metric('system.memory_available_gb', memory.available / (1024**3))
                self.record_metric('system.disk_percent', disk.percent)
                
                net_io = psutil.net_io_counters()
                self.record_metric('system.network_sent_mb', net_io.bytes_sent / (1024**2))
                self.record_metric('system.network_recv_mb', net_io.bytes_recv / (1024**2))
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"System monitoring error: {str(e)}")
                await asyncio.sleep(10)
    
    def record_metric(self, name: str, value: float):
        self.metrics[name].append({
            'timestamp': time.time(),
            'value': value
        })
    
    def record_operation(self, operation: str, duration: float, success: bool = True):
        self.record_metric(f'operation.{operation}.duration', duration)
        self.record_metric(f'operation.{operation}.{"success" if success else "failure"}', 1)
    
    def get_stats(self, metric_name: str, period_seconds: int = 60) -> Dict[str, float]:
        if metric_name not in self.metrics:
            return {}
        
        current_time = time.time()
        cutoff_time = current_time - period_seconds
        
        recent_values = [
            item['value'] for item in self.metrics[metric_name]
            if item['timestamp'] > cutoff_time
        ]
        
        if not recent_values:
            return {}
        
        return {
            'count': len(recent_values),
            'mean': sum(recent_values) / len(recent_values),
            'min': min(recent_values),
            'max': max(recent_values),
            'p50': sorted(recent_values)[len(recent_values) // 2],
            'p95': sorted(recent_values)[int(len(recent_values) * 0.95)],
            'p99': sorted(recent_values)[int(len(recent_values) * 0.99)]
        }
    
    def get_operation_stats(self, operation: str, period_seconds: int = 60) -> Dict[str, Any]:
        duration_stats = self.get_stats(f'operation.{operation}.duration', period_seconds)
        success_count = sum(
            1 for item in self.metrics[f'operation.{operation}.success']
            if item['timestamp'] > time.time() - period_seconds
        )
        failure_count = sum(
            1 for item in self.metrics[f'operation.{operation}.failure']
            if item['timestamp'] > time.time() - period_seconds
        )
        
        total_count = success_count + failure_count
        
        return {
            'operation': operation,
            'period_seconds': period_seconds,
            'total_count': total_count,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': success_count / total_count if total_count > 0 else 0,
            'duration_stats': duration_stats,
            'throughput': total_count / period_seconds if period_seconds > 0 else 0
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        cpu_stats = self.get_stats('system.cpu_percent', 60)
        memory_stats = self.get_stats('system.memory_percent', 60)
        
        health_status = 'healthy'
        issues = []
        
        if cpu_stats.get('mean', 0) > 80:
            health_status = 'degraded'
            issues.append('High CPU usage')
        
        if memory_stats.get('mean', 0) > 85:
            health_status = 'critical' if health_status == 'degraded' else 'degraded'
            issues.append('High memory usage')
        
        return {
            'status': health_status,
            'uptime_seconds': time.time() - self.start_time,
            'issues': issues,
            'metrics': {
                'cpu': cpu_stats,
                'memory': memory_stats,
                'disk': self.get_stats('system.disk_percent', 60),
                'network': {
                    'sent_mb': self.get_stats('system.network_sent_mb', 60),
                    'recv_mb': self.get_stats('system.network_recv_mb', 60)
                }
            }
        }
    
    def export_metrics(self) -> List[Dict[str, Any]]:
        exported = []
        current_time = time.time()
        
        for metric_name, values in self.metrics.items():
            for item in values:
                exported.append({
                    'metric': metric_name,
                    'timestamp': item['timestamp'],
                    'value': item['value'],
                    'age_seconds': current_time - item['timestamp']
                })
        
        return exported


class OperationTracker:
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None
        self.monitor.record_operation(self.operation_name, duration, success)
        return False


_performance_monitor: Optional[PerformanceMonitor] = None


async def get_performance_monitor() -> PerformanceMonitor:
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        await _performance_monitor.start()
    return _performance_monitor
