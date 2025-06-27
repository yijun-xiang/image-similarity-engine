import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

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

export const searchSimilarImages = async (
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

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};