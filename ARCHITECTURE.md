# System Architecture

## Overview

The Cluster Comparison Demo System is a modular, extensible framework for comparing different clustering strategies in support ticket search.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         ClusterComparison Component                  │   │
│  │  - Search Input                                       │   │
│  │  - Side-by-side Results                              │   │
│  │  - Smart Routing Display                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (app_main.py)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /search/tickets                                     │   │
│  │  /benchmark/stats                                    │   │
│  │  /health                                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Search      │  │  Clustering  │  │  Feedback    │
│  Module      │  │  Module      │  │  Module      │
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Neo4j     │
                    │   Database   │
                    └──────────────┘
```

## Data Flow

### 1. Data Generation Pipeline

```
generate_support_tickets.py
    │
    ├─> Generate 5000 tickets
    │   └─> support_tickets.jsonl
    │
    └─> Each ticket: {id, title, description, category, priority, status, created_at}
```

### 2. Embedding & Clustering Pipeline

```
cluster_tickets.py
    │
    ├─> Load tickets from JSONL
    │
    ├─> Generate embeddings (embedding_interface.py)
    │   ├─> Real: SentenceTransformer
    │   └─> Fallback: MockEmbedding (random vectors)
    │
    ├─> Cluster using three strategies:
    │   ├─> Type A: KMeans(k=5)      → Fast, coarse
    │   ├─> Type B: KMeans(k=20)     → Balanced
    │   └─> Type C: Agglomerative(100) → Fine-grained
    │
    └─> Output: clusters.json
        └─> {cluster_id, type, label, centroid, ticket_assignments}
```

### 3. Neo4j Ingestion Pipeline

```
ingest_clustered_tickets.py
    │
    ├─> Create Ticket nodes
    │   └─> (:Ticket {id, title, description, category, priority, status, created_at, embedding_vector})
    │
    ├─> Create Cluster nodes
    │   └─> (:Cluster {id, type, label, granularity_level, ticket_count, dominant_category, centroid})
    │
    └─> Create BELONGS_TO relationships
        └─> (:Ticket)-[:BELONGS_TO {cluster_type, assigned_at, similarity_score}]->(:Cluster)
```

### 4. Search Pipeline

```
search_tickets.py
    │
    ├─> Embed user query
    │
    ├─> Smart Routing (cluster_selection.py)
    │   └─> Select cluster types based on query analysis
    │
    ├─> For each selected cluster type:
    │   ├─> Find candidate clusters (query vs centroids)
    │   ├─> Retrieve tickets from candidates
    │   ├─> Compute similarity scores
    │   └─> Return top-k tickets
    │
    ├─> Apply feedback boosts (relevance_feedback.py)
    │
    └─> Return structured results
        └─> {query, results: {cluster_type_a: {...}, ...}, routing_info: {...}}
```

## Module Responsibilities

### Core Modules

| Module | Responsibility | Dependencies |
|--------|--------------|--------------|
| `generate_support_tickets.py` | Generate mock ticket data | None |
| `embedding_interface.py` | Abstract embedding model | sentence-transformers (optional) |
| `cluster_tickets.py` | Implement clustering strategies | scikit-learn, numpy |
| `ingest_clustered_tickets.py` | Load data into Neo4j | neo4j driver |
| `search_tickets.py` | Cluster-aware search | neo4j, embedding_interface |
| `cluster_selection.py` | Smart routing logic | None |
| `cluster_quality.py` | Quality metrics | neo4j, scipy |
| `relevance_feedback.py` | Feedback storage/retrieval | None |

### API Modules

| Module | Endpoint | Purpose |
|--------|----------|---------|
| `app/api/ticket_search.py` | POST /search/tickets | Search tickets |
| `app/api/benchmark.py` | GET /benchmark/stats | Get cluster statistics |

## Extension Points

### 1. Adding a New Clustering Strategy

**Location**: `backend/cluster_tickets.py`

```python
def cluster_type_d_custom(embeddings: np.ndarray) -> Dict[str, Any]:
    """
    Custom clustering strategy.
    
    Args:
        embeddings: Ticket embeddings (n_tickets, embedding_dim)
        
    Returns:
        Dictionary with cluster assignments and metadata
    """
    from sklearn.cluster import YourAlgorithm
    
    # Your clustering logic
    model = YourAlgorithm(n_clusters=50)
    labels = model.fit_predict(embeddings)
    
    # Generate metadata (follow existing pattern)
    clusters = generate_cluster_metadata(labels, embeddings, "D")
    
    return clusters
```

### 2. Adding a New Quality Metric

**Location**: `backend/cluster_quality.py`

```python
def compute_custom_metric(self, cluster_type: str) -> float:
    """
    Compute custom quality metric.
    
    Returns:
        Metric value
    """
    # Your metric computation
    pass

# Add to score_cluster_type():
def score_cluster_type(self, cluster_type: str) -> Dict[str, Any]:
    # ... existing metrics ...
    custom_metric = self.compute_custom_metric(cluster_type)
    
    return {
        'quality_score': quality_score,
        'intra_similarity': intra_similarity,
        'inter_distance': inter_distance,
        'custom_metric': custom_metric  # Add here
    }
```

### 3. Customizing Smart Routing

**Location**: `backend/cluster_selection.py`

```python
def select_clusters(self, query: str) -> Tuple[List[str], str]:
    # Add your custom logic before existing rules
    
    # Example: Custom domain-specific routing
    if 'payment' in query.lower() and 'refund' in query.lower():
        return ['C'], "Payment refund queries require fine-grained search"
    
    # ... existing logic ...
```

### 4. Adding New Search Features

**Location**: `backend/search_tickets.py`

```python
def _custom_filter_tickets(self, tickets: List[Dict], query: str) -> List[Dict]:
    """
    Custom ticket filtering logic.
    
    Example: Filter by date, category, etc.
    """
    # Your filtering logic
    return filtered_tickets

# Integrate into search_cluster_type():
def search_cluster_type(self, ...):
    # ... existing code ...
    
    # Apply custom filter
    tickets = self._custom_filter_tickets(tickets, query)
    
    # ... rest of search logic ...
```

## Mock Components

### MockEmbedding (`embedding_interface.py`)

**Purpose**: Provide embeddings when real model unavailable

**Implementation**: Generates random vectors with correct dimension

**Usage**: Automatically falls back if SentenceTransformer fails

**Limitations**: 
- Random vectors don't capture semantic meaning
- Useful for testing structure, not semantic search quality

**When to Use**:
- Testing without model dependencies
- Development when model unavailable
- Demonstrating system structure

## Performance Characteristics

### Clustering Performance

| Strategy | Algorithm | Complexity | Typical Time (5000 tickets) |
|----------|-----------|------------|----------------------------|
| Type A | K-Means (k=5) | O(n*k*d) | ~5 seconds |
| Type B | K-Means (k=20) | O(n*k*d) | ~15 seconds |
| Type C | Agglomerative (100) | O(n²*d) | ~2-5 minutes |

### Search Performance

| Cluster Type | Avg Latency | Candidates Scanned | Quality |
|--------------|-------------|-------------------|---------|
| Type A | ~50-100ms | ~800-1000 | Low |
| Type B | ~80-150ms | ~400-600 | Medium |
| Type C | ~150-250ms | ~200-400 | High |

*Note: Performance depends on query, data size, and hardware*

## Scalability Considerations

### Current Limitations

1. **Embedding Generation**: Linear with ticket count
   - Solution: Batch processing, caching
   
2. **Clustering Type C**: O(n²) complexity
   - Solution: Sampling for large datasets
   
3. **Neo4j Queries**: Can be slow without proper indexes
   - Solution: Indexes already created in schema

### Scaling Strategies

1. **Horizontal Scaling**: Multiple Neo4j instances
2. **Caching**: Cache embeddings and cluster assignments
3. **Sampling**: Use sample for Type C clustering on large datasets
4. **Async Processing**: Use async/await for I/O operations

## Security Considerations

1. **Neo4j Credentials**: Use environment variables
2. **API Endpoints**: Add authentication for production
3. **Input Validation**: Pydantic models validate inputs
4. **Error Handling**: Don't expose internal errors to clients

## Testing Strategy

### Unit Tests

- Test each module independently
- Mock external dependencies (Neo4j, embedding model)

### Integration Tests

- Test full pipeline: generate → cluster → ingest → search
- Test API endpoints

### Performance Tests

- Benchmark clustering algorithms
- Measure search latency
- Test with different data sizes

## Future Enhancements

1. **Real-time Updates**: Stream new tickets into clusters
2. **Incremental Clustering**: Update clusters without full recompute
3. **Multi-modal Search**: Add image/document search
4. **Advanced Feedback**: Learn from feedback to improve routing
5. **Visualization**: Graph visualization of clusters
6. **A/B Testing**: Compare clustering strategies in production



