import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface SearchResult {
  image_id: string;
  score: number;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  query_id: string;
  results: SearchResult[];
  total_found: number;
  search_time_ms: number;
  cached: boolean;
}

export interface IndexResponse {
  image_id: string;
  success: boolean;
  message: string;
  processing_time_ms: number;
}

export interface StatsResponse {
  collection: {
    name: string;
    vector_size: number;
    distance: string;
    points_count: number;
    segments_count: number;
  };
  cache: {
    connected_clients: number;
    used_memory: number;
    used_memory_human: string;
    keyspace_hits: number;
    keyspace_misses: number;
    total_commands_processed: number;
  };
  status: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  services: Record<string, string>;
}

export const searchImages = async (
  imageData: string,
  topK: number = 10,
  threshold: number = 0.0
): Promise<SearchResponse> => {
  const response = await api.post('/search', {
    image_data: imageData,
    top_k: topK,
    threshold: threshold,
    include_metadata: true,
  });
  return response.data;
};

export const indexImage = async (
  imageData: string,
  imageId?: string,
  metadata?: Record<string, any>
): Promise<IndexResponse> => {
  const response = await api.post('/index', {
    image_data: imageData,
    image_id: imageId,
    metadata: metadata || {},
  });
  return response.data;
};

export const getStats = async (): Promise<StatsResponse> => {
  const response = await api.get('/stats');
  return response.data;
};

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get('/health');
  return response.data;
};

export const deleteImage = async (imageId: string): Promise<void> => {
  await api.delete(`/index/${imageId}`);
};

api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;
