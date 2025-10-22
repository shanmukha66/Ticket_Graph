# Graph RAG API Documentation

FastAPI application for Graph-based Retrieval Augmented Generation.

## Quick Start

```bash
# From backend directory
cd backend

# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run the API
python app.py

# Or with uvicorn directly
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Access the API:
- **API Root**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Endpoints

### GET /
**Root endpoint with API information**

```bash
curl http://127.0.0.1:8000/
```

Response:
```json
{
  "name": "Graph RAG API",
  "version": "1.0.0",
  "endpoints": {
    "POST /ingest": "Run complete ingestion pipeline",
    "POST /ask": "Generate dual answers",
    "GET /graph/subgraph": "Get Cytoscape-friendly subgraph"
  }
}
```

---

### GET /health
**Health check for services**

```bash
curl http://127.0.0.1:8000/health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": {
      "status": "connected",
      "nodes": 1523
    },
    "vector_store": {
      "status": "loaded",
      "vectors": 7845
    }
  }
}
```

---

### POST /ingest
**Run complete ingestion pipeline**

Request body:
```json
{
  "csv_path": "/path/to/data.csv",
  "jsonl_path": "/path/to/data.jsonl",
  "similarity_threshold": 0.7,
  "similarity_top_k": 10,
  "community_algorithm": "louvain"
}
```

All fields are optional (defaults from env variables).

Example:
```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "similarity_threshold": 0.75,
    "similarity_top_k": 15,
    "community_algorithm": "louvain"
  }'
```

Response:
```json
{
  "status": "success",
  "statistics": {
    "csv_tickets": 500,
    "csv_sections": 2500,
    "jsonl_tickets": 1000,
    "jsonl_sections": 5000,
    "total_tickets": 1500,
    "total_sections": 7500,
    "similarity_edges": 12000,
    "communities": 25
  },
  "message": "Ingestion complete: 1500 tickets, 7500 sections, 12000 edges, 25 communities"
}
```

---

### POST /ask
**Generate dual answers (general + graph RAG)**

Request body:
```json
{
  "query": "How to fix authentication timeout issues?",
  "model": "gpt-4",
  "top_k_sections": 10,
  "num_hops": 1
}
```

Example:
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to fix authentication timeout issues?",
    "model": "gpt-4",
    "top_k_sections": 10,
    "num_hops": 1
  }'
```

Response:
```json
{
  "query": "How to fix authentication timeout issues?",
  
  "general": {
    "answer": "Authentication timeout issues can be addressed through...",
    "model": "gpt-4",
    "tokens": 450,
    "approach": "general"
  },
  
  "graph_rag": {
    "answer": "**Direct Answer**\nBased on ticket PROJ-4523...",
    "model": "gpt-4",
    "tokens": 1200,
    "approach": "graph_rag",
    "provenance": {
      "ticket_ids": ["PROJ-4523", "PROJ-6721", "PROJ-7834"],
      "section_ids": [...],
      "community_ids": [12, 15],
      "num_sections": 10,
      "num_tickets": 8,
      "num_communities": 2
    },
    "clusters": [
      {
        "cluster_id": 12,
        "size": 45,
        "reason": "Common themes: authentication, login, session, timeout",
        "top_tickets": ["PROJ-4523", "PROJ-6721", "PROJ-7834"]
      }
    ],
    "top_nodes": [
      {
        "id": "PROJ-4523",
        "summary": "Session timeout after 30 minutes",
        "degree": 8
      }
    ],
    "edges": {
      "total": 18,
      "threshold": 0.7,
      "description": "18 similarity connections used"
    },
    "reasoning": {
      "cluster_12": "Common themes: authentication, login, session, timeout"
    }
  },
  
  "provenance": {
    "ticket_ids": ["PROJ-4523", "PROJ-6721", "PROJ-7834"],
    "section_ids": [...],
    "community_ids": [12, 15]
  },
  
  "clusters": [
    {
      "cluster_id": 12,
      "size": 45,
      "reason": "Common themes: authentication, login, session, timeout"
    }
  ],
  
  "context_summary": {
    "sections_retrieved": 10,
    "tickets_involved": 8,
    "communities_analyzed": 2,
    "graph_nodes": 25,
    "graph_edges": 18
  }
}
```

---

### GET /graph/subgraph
**Get Cytoscape-friendly subgraph for visualization**

Query parameters:
- `query` (required): Search query
- `top_k` (optional, default=10): Number of sections to retrieve
- `num_hops` (optional, default=1): Graph traversal hops
- `include_communities` (optional, default=true): Include community info

Example:
```bash
curl "http://127.0.0.1:8000/graph/subgraph?query=authentication+issues&top_k=10&num_hops=1"
```

Response:
```json
{
  "nodes": [
    {
      "data": {
        "id": "PROJ-4523",
        "label": "Session timeout after 30 minutes",
        "type": "Ticket",
        "communityId": 12,
        "project": "AUTH",
        "status": "Resolved",
        "priority": "High",
        "score": 0.85
      }
    },
    {
      "data": {
        "id": "PROJ-4523_resolution",
        "label": "resolution",
        "type": "Section",
        "key": "resolution",
        "text": "Increased session timeout from 30 to 60 minutes..."
      }
    }
  ],
  
  "edges": [
    {
      "data": {
        "id": "PROJ-4523-has-PROJ-4523_resolution",
        "source": "PROJ-4523",
        "target": "PROJ-4523_resolution",
        "rel": "HAS_SECTION"
      }
    },
    {
      "data": {
        "id": "PROJ-4523-sim-PROJ-6721",
        "source": "PROJ-4523",
        "target": "PROJ-6721",
        "rel": "SIMILAR_TO",
        "score": 0.82
      }
    }
  ],
  
  "metadata": {
    "query": "authentication issues",
    "num_tickets": 8,
    "num_sections": 32,
    "num_edges": 45,
    "communities": [
      {
        "id": 12,
        "size": 45,
        "reason": "Common themes: authentication, login, session"
      }
    ]
  }
}
```

## Using with Cytoscape.js

The subgraph endpoint returns data in Cytoscape.js format. Use directly:

```javascript
fetch('http://127.0.0.1:8000/graph/subgraph?query=authentication')
  .then(res => res.json())
  .then(data => {
    const cy = cytoscape({
      container: document.getElementById('cy'),
      elements: {
        nodes: data.nodes,
        edges: data.edges
      },
      style: [
        {
          selector: 'node[type="Ticket"]',
          style: {
            'background-color': '#3b82f6',
            'label': 'data(label)'
          }
        },
        {
          selector: 'node[type="Section"]',
          style: {
            'background-color': '#10b981',
            'label': 'data(label)',
            'width': 20,
            'height': 20
          }
        },
        {
          selector: 'edge[rel="SIMILAR_TO"]',
          style: {
            'line-color': '#f59e0b',
            'width': 'data(score)',
            'width': edge => edge.data('score') * 5
          }
        }
      ]
    });
  });
```

## Python Client Examples

### Example 1: Ingest Data

```python
import requests

# Run ingestion
response = requests.post(
    "http://127.0.0.1:8000/ingest",
    json={
        "similarity_threshold": 0.7,
        "similarity_top_k": 10,
        "community_algorithm": "louvain"
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Tickets: {result['statistics']['total_tickets']}")
print(f"Communities: {result['statistics']['communities']}")
```

### Example 2: Ask Question

```python
import requests

# Ask question
response = requests.post(
    "http://127.0.0.1:8000/ask",
    json={
        "query": "How to debug memory leaks in Python?",
        "model": "gpt-4",
        "top_k_sections": 10,
        "num_hops": 1
    }
)

result = response.json()

# General answer
print("GENERAL ANSWER:")
print(result['general']['answer'])

# Graph RAG answer
print("\nGRAPH RAG ANSWER:")
print(result['graph_rag']['answer'])

# Provenance
print(f"\nBased on {len(result['provenance']['ticket_ids'])} tickets")
print(f"Communities: {result['provenance']['community_ids']}")

# Clusters
print("\nClusters involved:")
for cluster in result['clusters']:
    print(f"  - Cluster {cluster['cluster_id']}: {cluster['reason']}")
```

### Example 3: Get Subgraph

```python
import requests

# Get subgraph
response = requests.get(
    "http://127.0.0.1:8000/graph/subgraph",
    params={
        "query": "authentication timeout",
        "top_k": 10,
        "num_hops": 1,
        "include_communities": True
    }
)

result = response.json()

print(f"Nodes: {len(result['nodes'])}")
print(f"Edges: {len(result['edges'])}")
print(f"Communities: {len(result['metadata']['communities'])}")

# Print node IDs
print("\nTickets in subgraph:")
for node in result['nodes']:
    if node['data']['type'] == 'Ticket':
        print(f"  - {node['data']['id']}: {node['data']['label']}")
```

## CORS Configuration

To enable CORS for frontend access, update `app.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

All endpoints return standard HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid parameters)
- **404**: Not found (no results for query)
- **500**: Internal server error

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Performance

- **orjson**: 2-3x faster JSON serialization than standard json
- **Pydantic v2**: Fast validation and serialization
- **Async**: FastAPI async support for concurrent requests

## Deployment

### Development
```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Production
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Gunicorn
```bash
gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing

```bash
# Health check
curl http://127.0.0.1:8000/health

# Test ingestion (small sample)
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"similarity_threshold": 0.7}'

# Test query
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "model": "gpt-3.5-turbo"}'

# Test subgraph
curl "http://127.0.0.1:8000/graph/subgraph?query=test&top_k=5"
```

