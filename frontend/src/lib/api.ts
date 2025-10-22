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

export default api;
