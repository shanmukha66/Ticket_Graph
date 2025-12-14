/**
 * API client for Graph RAG backend
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface AskRequest {
  query: string;
  model?: string;
  top_k_sections?: number;
  num_hops?: number;
}

export interface GeneralAnswer {
  answer: string;
  model: string;
  tokens: number;
  approach: string;
}

export interface GraphRAGAnswer {
  answer: string;
  model: string;
  tokens: number;
  approach: string;
  provenance: {
    ticket_ids: string[];
    section_ids: string[];
    community_ids: number[];
    num_sections: number;
    num_tickets: number;
    num_communities: number;
  };
  clusters: Array<{
    cluster_id: number;
    size: number;
    reason: string;
    top_tickets: string[];
  }>;
  top_nodes: Array<{
    id: string;
    summary: string;
    degree: number;
  }>;
  edges: {
    total: number;
    threshold: number;
    description: string;
  };
  reasoning: Record<string, string>;
  context_summary: {
    sections_retrieved: number;
    tickets_involved: number;
    communities_analyzed: number;
    graph_nodes: number;
    graph_edges: number;
  };
}

export interface AskResponse {
  query: string;
  general: GeneralAnswer;
  graph_rag: GraphRAGAnswer;
  provenance: any;
  clusters: any[];
  context_summary: any;
}

export interface CytoscapeNode {
  data: {
    id: string;
    label: string;
    type: string;
    communityId?: number;
    project?: string;
    status?: string;
    priority?: string;
    score?: number;
    [key: string]: any;
  };
}

export interface CytoscapeEdge {
  data: {
    id: string;
    source: string;
    target: string;
    rel: string;
    score?: number;
  };
}

export interface SubgraphResponse {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
  metadata: {
    query: string;
    num_tickets: number;
    num_sections: number;
    num_edges: number;
    communities: Array<{
      id: number;
      size: number;
      reason: string;
    }>;
  };
}

export interface HealthResponse {
  status: string;
  services: {
    neo4j: {
      status: string;
      nodes: number;
    };
    vector_store: {
      status: string;
      vectors: number;
    };
  };
}

/**
 * Ask a question and get dual answers (general + graph RAG)
 */
export async function ask(request: AskRequest): Promise<AskResponse> {
  const response = await api.post<AskResponse>('/ask', request);
  return response.data;
}

/**
 * Fetch subgraph for visualization
 */
export async function fetchGraph(
  query: string,
  topK: number = 10,
  numHops: number = 1,
  includeCommunities: boolean = true
): Promise<SubgraphResponse> {
  const response = await api.get<SubgraphResponse>('/graph/subgraph', {
    params: {
      query,
      top_k: topK,
      num_hops: numHops,
      include_communities: includeCommunities,
    },
  });
  return response.data;
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
}

/**
 * Run ingestion pipeline
 */
export async function runIngestion(config: {
  csv_path?: string;
  jsonl_path?: string;
  similarity_threshold?: number;
  similarity_top_k?: number;
  community_algorithm?: string;
}): Promise<any> {
  const response = await api.post('/ingest', config);
  return response.data;
}

// Cluster search types
export interface ClusterSearchTicket {
  ticket_id: string;
  title: string;
  similarity: number;
}

export interface ClusterSearchResult {
  latency_ms: number;
  avg_similarity: number;
  num_candidates_scanned: number;
  top_k: ClusterSearchTicket[];
}

export interface ClusterSearchResponse {
  query: string;
  results: {
    cluster_type_a?: ClusterSearchResult;
    cluster_type_b?: ClusterSearchResult;
    cluster_type_c?: ClusterSearchResult;
  };
  routing_info?: {
    selected_clusters: string[];
    explanation: string;
    analysis: {
      query_length: number;
      precision_keywords: number;
      broad_keywords: number;
      technical_keywords: number;
      complexity_score: number;
    };
  };
  is_relevant?: boolean;
  relevance_message?: string;
}

/**
 * Search tickets using cluster-aware retrieval
 */
export async function searchTickets(
  query: string,
  top_k: number = 10,
  options?: {
    use_smart_routing?: boolean;
    apply_feedback_boost?: boolean;
    cluster_types?: ('A' | 'B' | 'C')[];
  }
): Promise<ClusterSearchResponse> {
  const payload: any = {
    query,
    top_k,
    use_smart_routing: options?.use_smart_routing ?? true,
    apply_feedback_boost: options?.apply_feedback_boost ?? true,
  };

  if (options?.cluster_types && options.cluster_types.length > 0) {
    payload.cluster_types = options.cluster_types;
  }

  const response = await api.post<ClusterSearchResponse>('/search/tickets', payload);
  return response.data;
}

// Clustering Demo types
export interface ClusterInfo {
  cluster_id: number;
  ticket_count: number;
  summary: string;
  sample_titles: string[];
}

export interface ClusteringResult {
  subset_size: number;
  algorithm: string;
  num_clusters: number;
  computation_time_ms: number;
  query_time_ms: number;
  total_time_ms: number;
  clusters: ClusterInfo[];
  metrics: {
    algorithm: string;
    n_clusters?: number;
    silhouette_score?: number;
    cluster_sizes?: Record<string, number>;
    avg_cluster_size?: number;
    min_cluster_size?: number;
    max_cluster_size?: number;
    num_noise_points?: number;
    eps?: number;
    min_samples?: number;
  };
  ticket_ids: string[];
}

export interface ClusteringResponse {
  query: string;
  results: Record<string, ClusteringResult>; // Key: "A_kmeans", "A_agglomerative", etc.
  summary: {
    total_combinations: number;
    fastest: string;
    fastest_time_ms: number;
    best_quality: string;
    best_quality_score: number;
    most_clusters: string;
    most_clusters_count: number;
  };
}

export interface ClusteringStats {
  total_tickets: number;
  tickets_with_embeddings: number;
  top_categories: Array<{ category: string; count: number }>;
  available_subset_sizes: number[];
  available_algorithms: string[];
}

/**
 * Run clustering on tickets relevant to a query
 * If subsetSize or algorithm is undefined, runs all combinations
 */
export async function runClustering(
  query: string,
  subsetSize?: number,
  algorithm?: 'kmeans' | 'agglomerative' | 'dbscan',
  topK: number = 1000
): Promise<ClusteringResponse> {
  const payload: any = {
    query: query,
    top_k: topK,
  };
  
  if (subsetSize !== undefined) {
    payload.subset_size = subsetSize;
  }
  
  if (algorithm !== undefined) {
    payload.algorithm = algorithm;
  }
  
  const response = await api.post<ClusteringResponse>('/clustering-demo/cluster', payload);
  return response.data;
}

/**
 * Get clustering statistics
 */
export async function getClusteringStats(): Promise<ClusteringStats> {
  const response = await api.get<ClusteringStats>('/clustering-demo/stats');
  return response.data;
}

export default api;
