import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize
import faiss
import pickle
import logging

logger = logging.getLogger(__name__)


class QueryOptimizer:
    def __init__(self, dimension: int = 512):
        self.dimension = dimension
        self.pca_model: Optional[PCA] = None
        self.index_flat: Optional[faiss.IndexFlatIP] = None
        self.index_ivf: Optional[faiss.IndexIVFFlat] = None
        self.quantizer: Optional[faiss.IndexFlatL2] = None
        self.reduced_dimension = min(256, dimension)
    
    async def initialize(self, sample_vectors: np.ndarray):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._initialize_sync, sample_vectors)
    
    def _initialize_sync(self, sample_vectors: np.ndarray):
        if len(sample_vectors) > 10000:
            self.pca_model = PCA(n_components=self.reduced_dimension)
            self.pca_model.fit(sample_vectors)
            logger.info(f"PCA model trained, reduced dimension: {self.reduced_dimension}")
        
        self.index_flat = faiss.IndexFlatIP(self.dimension)
        
        nlist = min(100, int(np.sqrt(len(sample_vectors))))
        self.quantizer = faiss.IndexFlatL2(self.dimension)
        self.index_ivf = faiss.IndexIVFFlat(self.quantizer, self.dimension, nlist)
        
        if len(sample_vectors) > 0:
            self.index_ivf.train(sample_vectors)
            logger.info(f"IVF index trained with {nlist} centroids")
    
    async def optimize_query_vector(self, query_vector: np.ndarray) -> np.ndarray:
        normalized = normalize(query_vector.reshape(1, -1))[0]
        
        if self.pca_model is not None:
            loop = asyncio.get_event_loop()
            reduced = await loop.run_in_executor(
                None, self.pca_model.transform, normalized.reshape(1, -1)
            )
            return reduced[0]
        
        return normalized
    
    async def build_optimized_index(self, vectors: np.ndarray, ids: List[str]) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._build_index_sync, vectors, ids)
    
    def _build_index_sync(self, vectors: np.ndarray, ids: List[str]) -> Dict[str, Any]:
        normalized_vectors = normalize(vectors)
        
        if len(vectors) < 10000:
            index = faiss.IndexFlatIP(self.dimension)
        else:
            nlist = int(np.sqrt(len(vectors)))
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            index.train(normalized_vectors)
        
        index.add(normalized_vectors)
        
        return {
            'index': index,
            'ids': ids,
            'size': len(vectors)
        }
    
    async def search_optimized(self, index_data: Dict[str, Any], query_vector: np.ndarray, 
                             k: int) -> List[Tuple[str, float]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._search_sync, index_data, query_vector, k
        )
    
    def _search_sync(self, index_data: Dict[str, Any], query_vector: np.ndarray, 
                    k: int) -> List[Tuple[str, float]]:
        index = index_data['index']
        ids = index_data['ids']
        
        normalized_query = normalize(query_vector.reshape(1, -1))
        
        if hasattr(index, 'nprobe'):
            index.nprobe = min(10, index.nlist)
        
        distances, indices = index.search(normalized_query, min(k, len(ids)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                results.append((ids[idx], float(dist)))
        
        return results
    
    def estimate_memory_usage(self, num_vectors: int) -> Dict[str, float]:
        vector_memory = num_vectors * self.dimension * 4 / (1024**3)
        
        if num_vectors < 10000:
            index_memory = vector_memory
        else:
            nlist = int(np.sqrt(num_vectors))
            index_memory = vector_memory + (nlist * self.dimension * 4 / (1024**3))
        
        return {
            'vector_memory_gb': vector_memory,
            'index_memory_gb': index_memory,
            'total_memory_gb': vector_memory + index_memory,
            'recommended_ram_gb': (vector_memory + index_memory) * 1.5
        }
    
    async def create_partitioned_index(self, vectors: np.ndarray, ids: List[str], 
                                     partitions: int = 4) -> List[Dict[str, Any]]:
        partition_size = len(vectors) // partitions
        tasks = []
        
        for i in range(partitions):
            start_idx = i * partition_size
            end_idx = start_idx + partition_size if i < partitions - 1 else len(vectors)
            
            partition_vectors = vectors[start_idx:end_idx]
            partition_ids = ids[start_idx:end_idx]
            
            task = asyncio.create_task(
                self.build_optimized_index(partition_vectors, partition_ids)
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def search_partitioned(self, partitioned_indices: List[Dict[str, Any]], 
                                query_vector: np.ndarray, k: int) -> List[Tuple[str, float]]:
        tasks = []
        for index_data in partitioned_indices:
            task = asyncio.create_task(
                self.search_optimized(index_data, query_vector, k * 2)
            )
            tasks.append(task)
        
        partition_results = await asyncio.gather(*tasks)
        
        all_results = []
        for results in partition_results:
            all_results.extend(results)
        
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        return all_results[:k]
