import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    job_id: str
    items: List[Any]
    callback: Optional[Callable] = None
    priority: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BatchProcessor:
    def __init__(self, batch_size: int = 1000, timeout: float = 5.0, max_workers: int = 10):
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_workers = max_workers
        self.queue = asyncio.PriorityQueue()
        self.workers = []
        self.results = defaultdict(list)
        self.running = False
    
    async def start(self):
        if self.running:
            return
        
        self.running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started {self.max_workers} batch workers")
    
    async def stop(self):
        self.running = False
        
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Batch processor stopped")
    
    async def submit_batch(self, job: BatchJob) -> str:
        priority = -job.priority
        await self.queue.put((priority, job))
        return job.job_id
    
    async def _worker(self, worker_id: str):
        batch_buffer = []
        last_flush = asyncio.get_event_loop().time()
        
        while self.running:
            try:
                try:
                    _, job = await asyncio.wait_for(
                        self.queue.get(), 
                        timeout=self.timeout
                    )
                    batch_buffer.append(job)
                except asyncio.TimeoutError:
                    pass
                
                current_time = asyncio.get_event_loop().time()
                should_flush = (
                    len(batch_buffer) >= self.batch_size or
                    (current_time - last_flush) >= self.timeout and batch_buffer
                )
                
                if should_flush:
                    await self._process_batch(worker_id, batch_buffer)
                    batch_buffer = []
                    last_flush = current_time
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, worker_id: str, jobs: List[BatchJob]):
        if not jobs:
            return
        
        start_time = asyncio.get_event_loop().time()
        total_items = sum(len(job.items) for job in jobs)
        
        logger.info(f"Worker {worker_id} processing batch: {len(jobs)} jobs, {total_items} items")
        
        try:
            grouped_jobs = defaultdict(list)
            for job in jobs:
                if job.callback:
                    key = id(job.callback)
                    grouped_jobs[key].append(job)
                else:
                    grouped_jobs[None].append(job)
            
            for callback_id, job_group in grouped_jobs.items():
                if callback_id is not None:
                    callback = job_group[0].callback
                    all_items = []
                    job_mapping = {}
                    
                    for job in job_group:
                        start_idx = len(all_items)
                        all_items.extend(job.items)
                        job_mapping[job.job_id] = (start_idx, len(job.items))
                    
                    results = await callback(all_items)
                    
                    for job in job_group:
                        start_idx, count = job_mapping[job.job_id]
                        job_results = results[start_idx:start_idx + count]
                        self.results[job.job_id] = job_results
            
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"Worker {worker_id} completed batch in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}")
            for job in jobs:
                self.results[job.job_id] = {'error': str(e)}
    
    async def get_results(self, job_id: str, timeout: float = 30.0) -> List[Any]:
        start_time = asyncio.get_event_loop().time()
        
        while job_id not in self.results:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Job {job_id} timed out")
            await asyncio.sleep(0.1)
        
        results = self.results.pop(job_id)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'queue_size': self.queue.qsize(),
            'active_workers': len(self.workers),
            'pending_results': len(self.results),
            'batch_size': self.batch_size,
            'timeout': self.timeout
        }


class DistributedBatchProcessor(BatchProcessor):
    def __init__(self, *args, redis_client=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_client = redis_client
        self.node_id = f"node_{asyncio.get_event_loop().time()}"
    
    async def submit_batch(self, job: BatchJob) -> str:
        if self.redis_client:
            serialized_job = {
                'job_id': job.job_id,
                'items': job.items,
                'priority': job.priority,
                'node_id': self.node_id,
                'created_at': job.created_at.isoformat()
            }
            
            await self.redis_client.lpush('batch_queue', json.dumps(serialized_job))
            await self.redis_client.expire('batch_queue', 3600)
            
        return await super().submit_batch(job)
    
    async def _distributed_worker(self, worker_id: str):
        while self.running:
            try:
                if self.redis_client:
                    job_data = await self.redis_client.brpop('batch_queue', timeout=1)
                    if job_data:
                        _, serialized = job_data
                        job_dict = json.loads(serialized)
                        
                        job = BatchJob(
                            job_id=job_dict['job_id'],
                            items=job_dict['items'],
                            priority=job_dict['priority'],
                            created_at=datetime.fromisoformat(job_dict['created_at'])
                        )
                        
                        await self.queue.put((-job.priority, job))
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Distributed worker error: {str(e)}")
                await asyncio.sleep(1)
