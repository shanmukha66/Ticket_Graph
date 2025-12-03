# Clustering Demo Implementation Guide

## Overview

This document describes the ticket clustering analytics demo that allows you to:
- Select ticket subsets (100, 500, or 1000 tickets)
- Choose clustering algorithms (K-Means, Agglomerative, DBSCAN)
- Run clustering and measure performance metrics
- Compare different combinations

## Files Created

### Backend

1. **`backend/app/api/clustering_demo.py`**
   - API endpoints for clustering operations
   - `/clustering-demo/cluster` - Run clustering on subset
   - `/clustering-demo/stats` - Get database statistics

2. **`backend/app_main.py`** (updated)
   - Added clustering_demo router

### Frontend

1. **`frontend/src/components/ClusteringDemo.tsx`**
   - Main UI component for clustering demo
   - Subset size selection (A=100, B=500, C=1000)
   - Algorithm selection (K-Means, Agglomerative, DBSCAN)
   - Results display with metrics
   - Comparison table

2. **`frontend/src/lib/api.ts`** (updated)
   - Added `runClustering()` function
   - Added `getClusteringStats()` function
   - TypeScript types for clustering responses

3. **`frontend/src/App.tsx`** (updated)
   - Added navigation tabs to switch between "Clustering Demo" and "Cluster Search"

## Integration Points

### Where to Plug in Real Embeddings

#### Backend: `backend/app/api/clustering_demo.py`

**Location 1: `get_embedding_model()` function (line ~50)**
```python
def get_embedding_model():
    """Get or load embedding model."""
    # TODO: Replace with your actual embedding model initialization
    # This is a placeholder - you should use your actual embedding service
    model_name = env("EMBED_MODEL", "intfloat/e5-base-v2")
    try:
        return SentenceTransformer(model_name)
    except Exception:
        # Fallback to a smaller model
        return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

**Action**: Replace with your actual embedding service initialization.

**Location 2: `run_clustering_demo()` endpoint (line ~250)**
```python
# Extract embeddings
# TODO: Replace this with your actual embedding retrieval logic
# If embeddings are already in Neo4j, use them. Otherwise, generate them.
embeddings_list = []
for ticket in tickets:
    if ticket['embedding_vector']:
        embeddings_list.append(ticket['embedding_vector'])
    else:
        # TODO: Generate embedding if not present
        # For now, we'll skip tickets without embeddings
        pass
```

**Action**: 
- If embeddings are stored in Neo4j, they're already being retrieved
- If you need to generate embeddings on-the-fly, add code here to call your embedding service

### Where to Plug in Real Neo4j Connections

#### Backend: `backend/app/api/clustering_demo.py`

**Location: `get_neo4j_driver()` function (line ~30)**
```python
def get_neo4j_driver():
    """Get Neo4j driver connection."""
    uri = env("NEO4J_URI", "bolt://localhost:7687")
    user = env("NEO4J_USER", "neo4j")
    password = env("NEO4J_PASSWORD", "password123")
    return GraphDatabase.driver(uri, auth=(user, password))
```

**Action**: 
- The function already uses environment variables
- Ensure your `.env` file has correct Neo4j credentials:
  ```
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_password
  ```

**Location: `get_ticket_subset()` function (line ~60)**
```python
def get_ticket_subset(driver, subset_size: int, ticket_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get a subset of tickets from Neo4j.
    ...
    """
    with driver.session() as session:
        # ... Cypher queries here
```

**Action**: 
- The function already queries Neo4j
- Ensure your Ticket nodes have `embedding_vector` property
- If your schema differs, update the Cypher queries

## How It Works

### Flow

1. **User selects subset size** (100, 500, or 1000 tickets)
2. **User selects algorithm** (K-Means, Agglomerative, or DBSCAN)
3. **Backend retrieves tickets** from Neo4j
4. **Backend extracts embeddings** from ticket nodes
5. **Backend runs clustering** algorithm
6. **Backend measures computation time**
7. **Backend queries Neo4j** to simulate cluster retrieval
8. **Backend measures query time**
9. **Backend generates cluster summaries** (keywords, sample titles)
10. **Frontend displays results** with metrics

### Clustering Algorithms

#### K-Means
- Number of clusters: 10 (100 tickets), 25 (500), 50 (1000)
- Fast, centroid-based clustering
- Good for balanced clusters

#### Agglomerative Clustering
- Number of clusters: 10 (100 tickets), 25 (500), 50 (1000)
- Hierarchical clustering with average linkage
- Uses cosine similarity metric
- Slower but produces high-quality clusters

#### DBSCAN
- Density-based clustering
- Automatically determines number of clusters
- Handles noise/outliers (assigns -1 label)
- Parameters tuned based on subset size

### Metrics Displayed

1. **Computation Time**: Time to run clustering algorithm (ms)
2. **Query Time**: Time to query Neo4j for cluster data (ms)
3. **Total Time**: Sum of computation + query time (ms)
4. **Number of Clusters**: Actual clusters created
5. **Silhouette Score**: Cluster quality metric (-1 to 1, higher is better)
6. **Cluster Sizes**: Min, max, and average tickets per cluster
7. **Noise Points**: For DBSCAN, number of outliers

### Comparison Feature

- Click "Add to Comparison" after running clustering
- Run multiple combinations (different subset sizes + algorithms)
- View side-by-side comparison table
- Compare metrics across all combinations

## Usage

### Starting the Backend

```bash
cd backend
python -m uvicorn app_main:app --host 127.0.0.1 --port 8001 --reload
```

### Starting the Frontend

```bash
cd frontend
npm install  # if not already done
npm run dev
```

### Accessing the Demo

1. Open browser to `http://localhost:5173`
2. Click on "Clustering Demo" tab
3. Select subset size (A=100, B=500, C=1000)
4. Select algorithm (K-Means, Agglomerative, DBSCAN)
5. Click "Run Clustering"
6. View results and metrics
7. Optionally add to comparison for side-by-side analysis

## Database Requirements

Your Neo4j database should have:

1. **Ticket nodes** with properties:
   - `id` (string, unique)
   - `title` (string)
   - `description` (string)
   - `category` (string)
   - `priority` (string)
   - `status` (string)
   - `created_at` (string)
   - `embedding_vector` (list of floats, 768 dimensions)

2. **Constraints** (already set up if you ran the schema setup):
   ```cypher
   CREATE CONSTRAINT ticket_id_unique IF NOT EXISTS
   FOR (t:Ticket) REQUIRE t.id IS UNIQUE;
   ```

## Troubleshooting

### "No embeddings found" error
- Ensure tickets in Neo4j have `embedding_vector` property
- Check that embeddings are stored as lists/arrays, not strings
- Verify embedding dimension matches (default: 768)

### "Not enough tickets in database" error
- Ensure you have at least the requested number of tickets
- Check that tickets have `embedding_vector IS NOT NULL`

### Slow clustering performance
- DBSCAN and Agglomerative are slower for large datasets
- Consider using K-Means for faster results
- Reduce subset size if needed

## Next Steps

1. **Generate embeddings** if not already in Neo4j
2. **Update embedding model** initialization if using a different service
3. **Customize cluster summaries** if you want different keyword extraction
4. **Add more metrics** if needed (e.g., cluster balance, variance)
5. **Store cluster assignments** in Neo4j if you want persistence

## API Endpoints

### POST `/clustering-demo/cluster`
Request:
```json
{
  "subset_size": 100,
  "algorithm": "kmeans",
  "ticket_ids": null  // optional
}
```

Response:
```json
{
  "subset_size": 100,
  "algorithm": "kmeans",
  "num_clusters": 10,
  "computation_time_ms": 45.2,
  "query_time_ms": 12.5,
  "total_time_ms": 57.7,
  "clusters": [...],
  "metrics": {...},
  "ticket_ids": [...]
}
```

### GET `/clustering-demo/stats`
Response:
```json
{
  "total_tickets": 5000,
  "tickets_with_embeddings": 5000,
  "top_categories": [...],
  "available_subset_sizes": [100, 500, 1000],
  "available_algorithms": ["kmeans", "agglomerative", "dbscan"]
}
```

