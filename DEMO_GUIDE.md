# Cluster Comparison Demo Guide

This guide explains how to run the complete cluster comparison demo system.

## Overview

The system demonstrates three clustering strategies for support ticket search:
- **Cluster Type A (Coarse)**: Fast, few large clusters (k=5)
- **Cluster Type B (Medium)**: Balanced speed and quality (k=20)
- **Cluster Type C (Fine-grained)**: High quality, many small clusters (n=100)

## Prerequisites

1. **Docker** - For running Neo4j
2. **Python 3.9+** - For backend
3. **Node.js 18+** - For frontend (optional)

## Quick Start

### 1. Start Neo4j

```bash
# Start Neo4j Docker container
./start_docker.sh

# Or manually:
docker-compose up -d neo4j
```

Wait for Neo4j to be ready (check http://localhost:7474)

### 2. Generate Mock Data

```bash
# Generate 5000 support tickets
python3 backend/generate_support_tickets.py --count 5000 --output data/support_tickets.jsonl
```

### 3. Generate Embeddings and Cluster

```bash
# This will:
# - Generate embeddings for all tickets
# - Create three clustering strategies
# - Store everything in Neo4j
python3 backend/cluster_tickets.py --input data/support_tickets.jsonl
```

### 4. Ingest into Neo4j

```bash
# Load tickets and clusters into Neo4j
python3 backend/ingest_clustered_tickets.py --tickets data/support_tickets.jsonl --clusters data/clusters.json
```

### 5. Run Complete Setup (Automated)

```bash
# One-command setup (recommended)
./setup_cluster_benchmark.sh
```

## Testing the System

### Test Search Function

```bash
# Search with all cluster types
python3 backend/search_tickets.py "login issue" 10

# Search with smart routing
python3 -c "
from backend.search_tickets import search_tickets
result = search_tickets('specific authentication error', top_k=5)
print(result)
"
```

### Test Cluster Selection

```bash
python3 backend/test_features.py
```

### Compute Cluster Quality

```bash
python3 backend/run_quality_scoring.py
```

### Test Relevance Feedback

```python
from backend.relevance_feedback import add_feedback, get_cluster_weights

# Add feedback
add_feedback("TICKET-10000", "login issue", "A", True)
add_feedback("TICKET-10001", "login issue", "B", False)

# Get updated weights
weights = get_cluster_weights()
print(weights)
```

## API Endpoints

### Start Backend Server

```bash
cd backend
uvicorn app_main:app --reload --port 8001
```

### Search Tickets

```bash
curl -X POST http://localhost:8001/search/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "query": "login issue",
    "top_k": 10,
    "use_smart_routing": true,
    "apply_feedback_boost": true
  }'
```

### Compute Quality Metrics

```bash
curl http://localhost:8001/benchmark/stats
```

## Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173 and use the ClusterComparison component.

## Example Outputs

### Search Result Format

```json
{
  "query": "login issue",
  "results": {
    "cluster_type_a": {
      "latency_ms": 120.5,
      "avg_similarity": 0.72,
      "num_candidates_scanned": 850,
      "top_k": [
        {
          "ticket_id": "TICKET-10000",
          "title": "Cannot login with email",
          "similarity": 0.81
        }
      ]
    },
    "cluster_type_b": { ... },
    "cluster_type_c": { ... }
  },
  "routing_info": {
    "selected_clusters": ["B"],
    "explanation": "Technical query detected - using Cluster Type B (balanced)"
  }
}
```

### Quality Metrics Format

```json
{
  "cluster_type_a": {
    "quality_score": "low",
    "intra_similarity": 0.60,
    "inter_distance": 0.45
  },
  "cluster_type_b": {
    "quality_score": "medium",
    "intra_similarity": 0.72,
    "inter_distance": 0.58
  },
  "cluster_type_c": {
    "quality_score": "high",
    "intra_similarity": 0.83,
    "inter_distance": 0.69
  }
}
```

## Architecture

```
┌─────────────────┐
│  Mock Data Gen  │ → support_tickets.jsonl
└─────────────────┘
         ↓
┌─────────────────┐
│   Embeddings    │ → embeddings.npy
└─────────────────┘
         ↓
┌─────────────────┐
│   Clustering    │ → clusters.json
│  (A, B, C)      │
└─────────────────┘
         ↓
┌─────────────────┐
│   Neo4j Ingest  │ → Neo4j Database
└─────────────────┘
         ↓
┌─────────────────┐
│  Search API     │ → Results
└─────────────────┘
```

## Troubleshooting

### Neo4j Connection Issues

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check connection
python3 -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123')); driver.verify_connectivity(); print('Connected!')"
```

### Embedding Model Issues

If the embedding model fails to load, the system will use mock embeddings automatically. Check `backend/embedding_interface.py` for details.

### Memory Issues

If clustering fails due to memory:
- Reduce ticket count: `--count 1000`
- Use mock embeddings: Set `USE_MOCK_EMBEDDINGS=true`

## Next Steps

1. Add more ticket categories
2. Implement custom clustering algorithms
3. Add more quality metrics
4. Build advanced feedback mechanisms
5. Add visualization components



