"""
Benchmarking API for comparing cluster query performance.
"""
import time
import numpy as np
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from backend.app.core.config import settings
from backend.utils.env import env


router = APIRouter(prefix="/benchmark", tags=["benchmark"])

# Global embedding model
_embedding_model = None


def get_embedding_model():
    """Lazy load embedding model."""
    global _embedding_model
    if _embedding_model is None:
        # Use configured embedding model, defaulting to correct E5 identifier
        model_name = settings.EMBEDDING_MODEL or env(
            "EMBED_MODEL",
            "intfloat/e5-base-v2"
        )
        print(f"[benchmark] Loading embedding model: {model_name}")
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def get_neo4j_driver():
    """Get Neo4j driver."""
    return GraphDatabase.driver(
        env("NEO4J_URI", "bolt://localhost:7687"),
        auth=(env("NEO4J_USER", "neo4j"), env("NEO4J_PASSWORD", "password123"))
    )


class BenchmarkQuery(BaseModel):
    """Benchmark query request."""
    query: str = Field(..., description="User query to benchmark")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")


class BenchmarkResult(BaseModel):
    """Benchmark result for a single cluster type."""
    latency_ms: float = Field(..., description="Query execution time in milliseconds")
    nodes_scanned: int = Field(..., description="Number of nodes scanned")
    avg_similarity: float = Field(..., description="Average similarity score")
    num_results: int = Field(..., description="Number of results returned")
    ticket_ids: List[str] = Field(default_factory=list, description="Returned ticket IDs")


class BenchmarkResponse(BaseModel):
    """Complete benchmark response."""
    query: str
    results: Dict[str, BenchmarkResult]
    best_cluster: str = Field(..., description="Best performing cluster type")


def query_cluster_type(
    driver,
    query_embedding: np.ndarray,
    cluster_type: str,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    Query a specific cluster type.
    
    Returns performance metrics and results.
    """
    start_time = time.time()
    
    with driver.session() as session:
        # Find most similar clusters by comparing query embedding to cluster centroids
        cluster_query = f"""
        MATCH (c:Cluster {{cluster_type: $cluster_type}})
        WITH c, c.centroid AS centroid
        WHERE centroid IS NOT NULL
        RETURN c.cluster_key AS cluster_key, c.cluster_id AS cluster_id
        ORDER BY c.cluster_key
        LIMIT 50
        """
        
        cluster_results = session.run(cluster_query, cluster_type=cluster_type)
        cluster_keys = [record['cluster_key'] for record in cluster_results]
        
        if not cluster_keys:
            return {
                'latency_ms': (time.time() - start_time) * 1000,
                'nodes_scanned': 0,
                'avg_similarity': 0.0,
                'num_results': 0,
                'ticket_ids': []
            }
        
        # Get tickets from top clusters
        # For simplicity, we'll get tickets from first few clusters
        # In production, you'd compute similarity to centroids first
        ticket_query = f"""
        MATCH (t:Ticket)-[r:BELONGS_TO {{cluster_type: $cluster_type}}]->(c:Cluster)
        WHERE c.cluster_key IN $cluster_keys
        WITH t, t.embedding AS embedding
        WHERE embedding IS NOT NULL
        RETURN t.id AS ticket_id, t.title AS title, t.description AS description, embedding
        LIMIT $limit
        """
        
        ticket_results = session.run(
            ticket_query,
            cluster_type=cluster_type,
            cluster_keys=cluster_keys[:10],  # Top 10 clusters
            limit=top_k * 3  # Get more to compute similarity
        )
        
        tickets = []
        embeddings = []
        for record in ticket_results:
            tickets.append({
                'id': record['ticket_id'],
                'title': record['title'],
                'description': record['description']
            })
            embeddings.append(record['embedding'])
        
        nodes_scanned = len(tickets)
        
        # Compute similarities
        if embeddings:
            embeddings_array = np.array(embeddings)
            similarities = np.dot(embeddings_array, query_embedding)
            
            # Get top-k by similarity
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            top_tickets = [tickets[i] for i in top_indices]
            top_similarities = similarities[top_indices]
            
            avg_similarity = float(np.mean(top_similarities))
            ticket_ids = [t['id'] for t in top_tickets]
        else:
            avg_similarity = 0.0
            ticket_ids = []
            top_tickets = []
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'latency_ms': latency_ms,
            'nodes_scanned': nodes_scanned,
            'avg_similarity': avg_similarity,
            'num_results': len(top_tickets),
            'ticket_ids': ticket_ids
        }


@router.post("/query", response_model=BenchmarkResponse)
async def benchmark_query(request: BenchmarkQuery) -> BenchmarkResponse:
    """
    Benchmark query performance across all three cluster types.
    
    Returns performance metrics for Cluster A, B, and C.
    """
    # Generate query embedding
    model = get_embedding_model()
    query_embedding = model.encode(
        request.query,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    
    # Get Neo4j driver
    driver = get_neo4j_driver()
    
    try:
        results = {}
        
        # Query each cluster type
        for cluster_type in ['A', 'B', 'C']:
            result = query_cluster_type(
                driver,
                query_embedding,
                cluster_type,
                request.top_k
            )
            results[cluster_type] = BenchmarkResult(**result)
        
        # Determine best cluster (highest similarity, reasonable latency)
        # Score = similarity * (1 - normalized_latency)
        cluster_scores = {}
        max_latency = max(r.latency_ms for r in results.values())
        
        for cluster_type, result in results.items():
            normalized_latency = result.latency_ms / max_latency if max_latency > 0 else 0
            score = result.avg_similarity * (1 - normalized_latency * 0.3)  # Weight latency less
            cluster_scores[cluster_type] = score
        
        best_cluster = max(cluster_scores, key=cluster_scores.get)
        
        return BenchmarkResponse(
            query=request.query,
            results={
                'clusterA': results['A'],
                'clusterB': results['B'],
                'clusterC': results['C']
            },
            best_cluster=best_cluster
        )
    
    finally:
        driver.close()


@router.get("/stats")
async def get_benchmark_stats() -> Dict[str, Any]:
    """Get statistics about clusters in the database."""
    driver = get_neo4j_driver()
    
    try:
        with driver.session() as session:
            stats = {}
            
            for cluster_type in ['A', 'B', 'C']:
                query = """
                MATCH (c:Cluster {cluster_type: $cluster_type})
                RETURN count(c) AS cluster_count,
                       avg(c.ticket_count) AS avg_tickets_per_cluster,
                       min(c.ticket_count) AS min_tickets,
                       max(c.ticket_count) AS max_tickets
                """
                result = session.run(query, cluster_type=cluster_type).single()
                
                stats[f"cluster_{cluster_type}"] = {
                    'num_clusters': result['cluster_count'],
                    'avg_tickets_per_cluster': float(result['avg_tickets_per_cluster'] or 0),
                    'min_tickets': result['min_tickets'],
                    'max_tickets': result['max_tickets']
                }
            
            # Total tickets
            ticket_count = session.run("MATCH (t:Ticket) RETURN count(t) AS count").single()['count']
            stats['total_tickets'] = ticket_count
            
            return stats
    
    finally:
        driver.close()

