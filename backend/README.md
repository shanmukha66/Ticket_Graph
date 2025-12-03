# Backend Code Structure

This document explains the modular structure of the backend codebase.

## Core Modules

### 1. Data Generation (`generate_support_tickets.py`)

**Purpose**: Generate realistic mock support tickets

**Key Functions**:
- `generate_support_ticket(index, category)`: Generate a single ticket
- `generate_ticket_id(index)`: Create unique ticket IDs
- `generate_timestamp()`: Create realistic timestamps

**Output**: JSONL file with tickets containing:
- `id`, `title`, `description`, `category`, `priority`, `status`, `created_at`

**Usage**:
```python
from backend.generate_support_tickets import generate_support_ticket

ticket = generate_support_ticket(0, "login issue")
```

**Mocked Components**: None (all data is generated)

---

### 2. Embedding Interface (`embedding_interface.py`)

**Purpose**: Abstract embedding model interface (supports real or mock models)

**Key Classes**:
- `EmbeddingModel` (ABC): Base interface
- `SentenceTransformerEmbedding`: Real model wrapper
- `MockEmbedding`: Mock implementation for testing

**Key Methods**:
- `embed_query(query)`: Embed a single query
- `embed_documents(documents)`: Embed multiple documents
- `get_sentence_embedding_dimension()`: Get embedding size

**Usage**:
```python
from backend.embedding_interface import SentenceTransformerEmbedding, MockEmbedding

# Real model
model = SentenceTransformerEmbedding()

# Mock model (for testing)
mock_model = MockEmbedding(dimension=768)
```

**Mocked Components**: 
- `MockEmbedding` generates random vectors (documented in class docstring)
- Automatically falls back to mock if real model fails to load

---

### 3. Clustering (`cluster_tickets.py`)

**Purpose**: Implement three clustering strategies

**Key Functions**:
- `cluster_type_a_coarse(embeddings)`: K-Means with k=5
- `cluster_type_b_medium(embeddings)`: K-Means with k=20
- `cluster_type_c_fine(embeddings)`: Agglomerative with n=100

**Key Classes**:
- `ClusterMetadata`: Stores cluster information

**Output**: JSON file with cluster assignments and metadata

**Usage**:
```python
from backend.cluster_tickets import cluster_type_a_coarse

clusters = cluster_type_a_coarse(embeddings)
```

**Trade-offs Documented**:
- Type A: Fastest, lowest quality
- Type B: Balanced
- Type C: Slowest, highest quality

---

### 4. Neo4j Ingestion (`ingest_clustered_tickets.py`)

**Purpose**: Load tickets and clusters into Neo4j

**Key Functions**:
- `ingest_tickets(session, tickets)`: Create Ticket nodes
- `ingest_clusters(session, clusters)`: Create Cluster nodes
- `create_belongs_to_relationships(session, assignments)`: Link tickets to clusters

**Schema**:
- `(:Ticket {id, title, description, category, priority, status, created_at, embedding_vector})`
- `(:Cluster {id, type, label, granularity_level, ticket_count, dominant_category, centroid})`
- `(:Ticket)-[:BELONGS_TO {cluster_type, assigned_at, similarity_score}]->(:Cluster)`

**Usage**:
```python
from backend.ingest_clustered_tickets import ingest_all

ingest_all(tickets_file, clusters_file)
```

---

### 5. Search (`search_tickets.py`)

**Purpose**: Cluster-aware ticket search

**Key Classes**:
- `TicketSearcher`: Main search class

**Key Methods**:
- `embed_query(query)`: Embed user query
- `_find_candidate_clusters(query_embedding, cluster_type)`: Find relevant clusters
- `_retrieve_and_rank_tickets(query_embedding, clusters, cluster_type)`: Get and rank tickets
- `search_cluster_type(query_embedding, cluster_type, top_k)`: Search one cluster type
- `search_tickets(query, top_k, ...)`: Search all cluster types

**Usage**:
```python
from backend.search_tickets import search_tickets

result = search_tickets("login issue", top_k=10)
```

**Features**:
- Smart routing (automatic cluster selection)
- Feedback boost (adjusts scores based on user feedback)

---

### 6. Cluster Selection (`cluster_selection.py`)

**Purpose**: Smart routing based on query analysis

**Key Classes**:
- `ClusterSelector`: Analyzes queries and selects optimal cluster types

**Key Methods**:
- `analyze_query(query)`: Analyze query characteristics
- `select_clusters(query)`: Select cluster types based on analysis

**Decision Factors**:
- Query length
- Keyword presence (precision, broad, technical)
- Complexity score

**Usage**:
```python
from backend.cluster_selection import select_cluster_strategy

result = select_cluster_strategy("specific authentication error")
# Returns: {'selected_clusters': ['C'], 'explanation': '...'}
```

---

### 7. Cluster Quality (`cluster_quality.py`)

**Purpose**: Compute cluster quality metrics

**Key Classes**:
- `ClusterQualityScorer`: Computes quality metrics

**Key Methods**:
- `compute_intra_cluster_similarity(cluster_type)`: Homogeneity metric
- `compute_inter_cluster_distance(cluster_type)`: Separation metric
- `compute_quality_score(intra, inter)`: Overall quality score
- `score_all_clusters()`: Score all cluster types

**Metrics**:
- Intra-cluster similarity: Average similarity within clusters (0-1)
- Inter-cluster distance: Average distance between centroids (0-2)
- Quality score: "low", "medium", or "high"

**Usage**:
```python
from backend.cluster_quality import compute_cluster_quality

metrics = compute_cluster_quality()
```

---

### 8. Relevance Feedback (`relevance_feedback.py`)

**Purpose**: Store and use user feedback

**Key Classes**:
- `RelevanceFeedbackStore`: Manages feedback storage

**Key Methods**:
- `add_feedback(ticket_id, query, cluster_type, is_relevant)`: Store feedback
- `compute_cluster_weights()`: Calculate weights based on feedback
- `compute_ticket_boost(ticket_id)`: Calculate boost score for ticket

**Storage**: JSON file (`mnt/data/feedback.json`)

**Usage**:
```python
from backend.relevance_feedback import add_feedback, get_cluster_weights

add_feedback("TICKET-10000", "login issue", "A", True)
weights = get_cluster_weights()
```

---

## Helper Modules

### `utils/env.py`

**Purpose**: Environment variable management

**Usage**:
```python
from backend.utils.env import env

neo4j_uri = env("NEO4J_URI", "bolt://localhost:7687")
```

---

## API Endpoints (`app/api/`)

### `ticket_search.py`

**Endpoint**: `POST /search/tickets`

**Request**:
```json
{
  "query": "login issue",
  "top_k": 10,
  "use_smart_routing": true,
  "apply_feedback_boost": true
}
```

**Response**: See `DEMO_GUIDE.md` for format

---

## Extension Points

### Adding a New Clustering Strategy

1. Add function in `cluster_tickets.py`:
```python
def cluster_type_d_custom(embeddings):
    # Your clustering logic
    pass
```

2. Update ingestion to handle new type
3. Update search to include new type

### Adding New Quality Metrics

1. Add method to `ClusterQualityScorer`:
```python
def compute_custom_metric(self, cluster_type):
    # Your metric logic
    pass
```

2. Include in `score_cluster_type()` output

### Customizing Smart Routing

1. Modify `ClusterSelector.select_clusters()`:
```python
# Add your custom logic
if custom_condition:
    return ['C'], "Custom explanation"
```

---

## Testing

Run all tests:
```bash
python3 backend/test_features.py
```

Test individual components:
```python
# Test clustering
python3 backend/cluster_tickets.py --input data/tickets.jsonl

# Test search
python3 backend/search_tickets.py "test query" 10

# Test quality
python3 backend/run_quality_scoring.py
```

---

## Performance Considerations

- **Embedding Generation**: Can be slow for large datasets. Consider caching.
- **Clustering**: Type C (Agglomerative) is O(n²), use sampling for very large datasets.
- **Neo4j Queries**: Use indexes (already created in schema).
- **Search**: Cluster-aware search reduces candidates significantly.

---

## Mock Components Summary

| Component | Mocked? | Location | Notes |
|-----------|---------|----------|-------|
| Embeddings | Optional | `embedding_interface.py` | Falls back to mock if model fails |
| Data | No | `generate_support_tickets.py` | All data is generated, not mocked |
| Neo4j | No | Uses real Neo4j | Requires Docker |
| Clustering | No | Uses scikit-learn | Real algorithms |
