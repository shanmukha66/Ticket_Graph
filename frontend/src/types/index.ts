export interface Node {
  id: string
  label: string
  properties: Record<string, any>
}

export interface Relationship {
  id: string
  type: string
  from_node: string
  to_node: string
  properties: Record<string, any>
}

export interface GraphData {
  nodes: Node[]
  relationships: Relationship[]
}

export interface SearchResult {
  id: string
  text: string
  score: number
  metadata: Record<string, any>
}

export interface SearchResponse {
  results: SearchResult[]
  query: string
}

