"""
Clustering Demo API endpoints for ticket analytics.

This module provides endpoints for:
- Selecting ticket subsets (100, 500, 1000 tickets)
- Running clustering algorithms (K-Means, Agglomerative, DBSCAN)
- Measuring performance metrics (computation time, query time)
- Retrieving cluster information from Neo4j
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import time
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score
from neo4j import GraphDatabase
from backend.utils.env import env
from sentence_transformers import SentenceTransformer


router = APIRouter(prefix="/clustering-demo", tags=["clustering-demo"])


# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================

class ClusteringRequest(BaseModel):
    """Request model for clustering operation."""
    query: str = Field(..., description="Search query to find relevant tickets")
    subset_size: Optional[int] = Field(default=None, description="Number of tickets to cluster: 100, 500, or 1000. If None, runs all three.")
    algorithm: Optional[str] = Field(default=None, description="Clustering algorithm: 'kmeans', 'agglomerative', or 'dbscan'. If None, runs all three.")
    top_k: int = Field(default=100, description="Number of top tickets to retrieve for clustering", ge=10, le=1000)


class ClusterInfo(BaseModel):
    """Information about a single cluster."""
    cluster_id: int
    ticket_count: int
    summary: str  # Top keywords or sample titles
    sample_titles: List[str]  # Sample ticket titles from cluster


class ClusteringResponse(BaseModel):
    """Response model for clustering operation."""
    query: str
    results: Dict[str, Dict[str, Any]]  # Key: "A_kmeans", "A_agglomerative", etc.
    summary: Dict[str, Any]  # Overall summary statistics


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_neo4j_driver():
    """Get Neo4j driver connection."""
    uri = env("NEO4J_URI", "bolt://localhost:7687")
    user = env("NEO4J_USER", "neo4j")
    password = env("NEO4J_PASSWORD", "password123")
    return GraphDatabase.driver(uri, auth=(user, password))


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


def get_tickets_by_query(driver, query: str, top_k: int) -> List[Dict[str, Any]]:
    """
    Get tickets relevant to a query using vector similarity search.
    
    Args:
        driver: Neo4j driver
        query: Search query string
        top_k: Number of top tickets to retrieve
    
    Returns:
        List of ticket dictionaries sorted by relevance
    """
    # TODO: Replace with your actual embedding model
    model = get_embedding_model()
    query_embedding = model.encode(query, normalize_embeddings=True, show_progress_bar=False)
    
    with driver.session() as session:
        # Get all tickets with embeddings and compute similarity
        # Check for both embedding_vector and embedding properties
        query_cypher = """
        MATCH (t:Ticket)
        WHERE t.embedding_vector IS NOT NULL OR t.embedding IS NOT NULL
        RETURN t.id AS id,
               t.title AS title,
               t.description AS description,
               t.category AS category,
               t.priority AS priority,
               t.status AS status,
               t.created_at AS created_at,
               COALESCE(t.embedding_vector, t.embedding) AS embedding_vector
        """
        result = session.run(query_cypher)
        
        tickets_with_similarity = []
        for record in result:
            embedding_vector = record['embedding_vector']
            
            # Skip if embedding is None or empty
            if embedding_vector is None or len(embedding_vector) == 0:
                continue
            
            try:
                ticket_embedding = np.array(embedding_vector)
                # Ensure it's a 1D array
                if ticket_embedding.ndim > 1:
                    ticket_embedding = ticket_embedding.flatten()
                
                # Check dimensions match
                if len(ticket_embedding) != len(query_embedding):
                    print(f"Warning: Embedding dimension mismatch for ticket {record['id']}: {len(ticket_embedding)} vs {len(query_embedding)}")
                    continue
                
                similarity = float(np.dot(query_embedding, ticket_embedding))
                
                tickets_with_similarity.append({
                    'id': record['id'],
                    'title': record['title'] or '',
                    'description': record['description'] or '',
                    'category': record['category'] or 'unknown',
                    'priority': record['priority'] or 'medium',
                    'status': record['status'] or 'open',
                    'created_at': record['created_at'] or '',
                    'embedding_vector': embedding_vector,
                    'similarity': similarity
                })
            except Exception as e:
                print(f"Error processing ticket {record['id']}: {str(e)}")
                continue
        
        # Sort by similarity and return top_k
        tickets_with_similarity.sort(key=lambda x: x['similarity'], reverse=True)
        return tickets_with_similarity[:top_k]


def get_ticket_subset(driver, subset_size: int, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get a subset of tickets from a list.
    
    Args:
        driver: Neo4j driver (unused, kept for compatibility)
        subset_size: Number of tickets to retrieve (100, 500, or 1000)
        tickets: List of tickets to subset from
    
    Returns:
        List of ticket dictionaries (first subset_size tickets)
    """
    return tickets[:subset_size]


def run_clustering(embeddings: np.ndarray, algorithm: str, subset_size: int) -> tuple:
    """
    Run clustering algorithm on embeddings.
    
    Args:
        embeddings: Numpy array of embeddings (n_samples, n_features)
        algorithm: Algorithm name ('kmeans', 'agglomerative', 'dbscan')
        subset_size: Size of subset (used to determine number of clusters)
    
    Returns:
        Tuple of (labels, metrics_dict, computation_time_ms)
    """
    start_time = time.time()
    
    # Determine number of clusters based on subset size
    # For 100 tickets: ~10 clusters, 500: ~25 clusters, 1000: ~50 clusters
    if subset_size == 100:
        n_clusters = 10
    elif subset_size == 500:
        n_clusters = 25
    else:  # 1000
        n_clusters = 50
    
    labels = None
    metrics = {}
    
    if algorithm.lower() == 'kmeans':
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)
        metrics['algorithm'] = 'K-Means'
        metrics['n_clusters'] = n_clusters
        
    elif algorithm.lower() == 'agglomerative':
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage='average',
            metric='cosine'
        )
        labels = clustering.fit_predict(embeddings)
        metrics['algorithm'] = 'Agglomerative Clustering'
        metrics['n_clusters'] = n_clusters
        
    elif algorithm.lower() == 'dbscan':
        # DBSCAN doesn't take n_clusters, so we estimate eps
        from sklearn.neighbors import NearestNeighbors
        n_neighbors = min(10, len(embeddings) - 1)
        neighbors = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
        neighbors.fit(embeddings)
        distances, _ = neighbors.kneighbors(embeddings)
        distances = distances[:, 1:]  # Exclude self
        eps = float(np.percentile(distances, 70))
        min_samples = max(3, int(subset_size * 0.05))  # 5% of subset size
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine', algorithm='brute')
        labels = dbscan.fit_predict(embeddings)
        
        unique_labels = set(labels)
        if -1 in unique_labels:
            unique_labels.remove(-1)  # Exclude noise
        num_clusters = len(unique_labels)
        
        metrics['algorithm'] = 'DBSCAN'
        metrics['n_clusters'] = num_clusters
        metrics['num_noise_points'] = int(np.sum(labels == -1))
        metrics['eps'] = eps
        metrics['min_samples'] = min_samples
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    computation_time = (time.time() - start_time) * 1000  # Convert to ms
    
    # Calculate quality metrics
    unique_labels_set = set(labels)
    if -1 in unique_labels_set:
        unique_labels_set.remove(-1)
    
    if len(unique_labels_set) > 1:
        # Calculate silhouette score (excluding noise for DBSCAN)
        non_noise_mask = labels != -1
        if np.sum(non_noise_mask) > 1:
            metrics['silhouette_score'] = float(silhouette_score(
                embeddings[non_noise_mask],
                labels[non_noise_mask]
            ))
        else:
            metrics['silhouette_score'] = 0.0
    else:
        metrics['silhouette_score'] = 0.0
    
    # Calculate cluster sizes
    cluster_sizes = {}
    for label in unique_labels_set:
        cluster_sizes[int(label)] = int(np.sum(labels == label))
    metrics['cluster_sizes'] = cluster_sizes
    metrics['avg_cluster_size'] = float(np.mean(list(cluster_sizes.values()))) if cluster_sizes else 0
    metrics['min_cluster_size'] = int(np.min(list(cluster_sizes.values()))) if cluster_sizes else 0
    metrics['max_cluster_size'] = int(np.max(list(cluster_sizes.values()))) if cluster_sizes else 0
    
    return labels, metrics, computation_time


def generate_cluster_summary(tickets: List[Dict], labels: np.ndarray, cluster_id: int) -> tuple:
    """
    Generate summary for a cluster.
    
    Returns:
        Tuple of (summary_text, sample_titles)
    """
    cluster_indices = np.where(labels == cluster_id)[0]
    cluster_tickets = [tickets[i] for i in cluster_indices]
    
    # Get sample titles
    sample_titles = [t['title'] for t in cluster_tickets[:5]]  # First 5 titles
    
    # Extract keywords from titles and descriptions
    all_text = ' '.join([t['title'] + ' ' + t['description'] for t in cluster_tickets])
    words = all_text.lower().split()
    # Simple keyword extraction (top words excluding common stop words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'not', 'no', 'error', 'issue', 'problem', 'bug', 'fix', 'unable', 'cannot'}
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    from collections import Counter
    top_keywords = [word for word, count in Counter(keywords).most_common(5)]
    
    summary = f"Keywords: {', '.join(top_keywords[:5])}" if top_keywords else "No keywords extracted"
    
    return summary, sample_titles


def query_clusters_from_neo4j(driver, ticket_ids: List[str], labels: np.ndarray) -> float:
    """
    Query Neo4j to get cluster information.
    This simulates querying clusters from the database.
    
    Returns:
        Query execution time in milliseconds
    """
    start_time = time.time()
    
    with driver.session() as session:
        # Example query: Get tickets with their properties
        # In a real scenario, you might store cluster assignments in Neo4j
        query = """
        MATCH (t:Ticket)
        WHERE t.id IN $ticket_ids
        RETURN t.id AS id,
               t.title AS title,
               t.category AS category,
               t.priority AS priority,
               t.status AS status
        """
        result = session.run(query, ticket_ids=ticket_ids)
        tickets = [record for record in result]
    
    query_time = (time.time() - start_time) * 1000  # Convert to ms
    return query_time


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@router.post("/cluster", response_model=ClusteringResponse)
async def run_clustering_demo(request: ClusteringRequest):
    """
    Run clustering on tickets relevant to a query.
    
    Runs all combinations of:
    - Subset sizes: A=100, B=500, C=1000
    - Algorithms: K-Means, Agglomerative, DBSCAN
    
    This endpoint:
    1. Retrieves top-k tickets relevant to the query
    2. Runs all 9 combinations (3 subsets × 3 algorithms)
    3. Measures computation time and query time for each
    4. Returns all results for comparison
    """
    try:
        driver = get_neo4j_driver()
        
        # Step 1: Get tickets relevant to query
        print(f"\n[Clustering Demo] Getting top {request.top_k} tickets for query: '{request.query}'...")
        try:
            all_tickets = get_tickets_by_query(driver, request.query, request.top_k)
            print(f"[Clustering Demo] Retrieved {len(all_tickets)} tickets from Neo4j")
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve tickets from Neo4j: {str(e)}"
            )
        
        if len(all_tickets) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough tickets found for query. Found {len(all_tickets)} tickets with embeddings, need at least 100. Please ensure tickets have embedding_vector property in Neo4j."
            )
        
        # Extract embeddings
        embeddings_list = []
        valid_tickets = []
        for ticket in all_tickets:
            embedding_vector = ticket.get('embedding_vector')
            if embedding_vector is not None and len(embedding_vector) > 0:
                try:
                    # Convert to numpy array and validate
                    emb_array = np.array(embedding_vector)
                    if emb_array.ndim > 1:
                        emb_array = emb_array.flatten()
                    # Check if it's a valid embedding (not all zeros, reasonable dimension)
                    if len(emb_array) > 0 and np.any(emb_array != 0):
                        embeddings_list.append(emb_array.tolist())
                        valid_tickets.append(ticket)
                except Exception as e:
                    print(f"Warning: Skipping ticket {ticket.get('id')} due to embedding error: {str(e)}")
                    continue
        
        if not embeddings_list:
            raise HTTPException(
                status_code=400,
                detail=f"No valid embeddings found. Found {len(all_tickets)} tickets but none have valid embedding_vector property. Please ensure tickets have embedding_vector property with non-zero values."
            )
        
        print(f"[Clustering Demo] Found {len(valid_tickets)} tickets with valid embeddings")
        
        try:
            all_embeddings = np.array(embeddings_list)
            # Normalize embeddings if needed
            norms = np.linalg.norm(all_embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            all_embeddings = all_embeddings / norms
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process embeddings: {str(e)}"
            )
        
        # Determine which combinations to run
        subset_sizes = [100, 500, 1000] if request.subset_size is None else [request.subset_size]
        algorithms = ['kmeans', 'agglomerative', 'dbscan'] if request.algorithm is None else [request.algorithm]
        
        # Step 2: Run all combinations
        results = {}
        all_metrics = []
        
        for subset_size in subset_sizes:
            if len(valid_tickets) < subset_size:
                continue  # Skip if not enough tickets
            
            subset_tickets = valid_tickets[:subset_size]
            subset_embeddings = all_embeddings[:subset_size]
            
            for algorithm in algorithms:
                key = f"{'A' if subset_size == 100 else 'B' if subset_size == 500 else 'C'}_{algorithm}"
                
                print(f"[Clustering Demo] Running {key} ({subset_size} tickets, {algorithm})...")
                
                try:
                    # Run clustering
                    labels, metrics, computation_time = run_clustering(
                        subset_embeddings,
                        algorithm,
                        subset_size
                    )
                    
                    # Query Neo4j
                    ticket_ids = [t['id'] for t in subset_tickets]
                    query_time = query_clusters_from_neo4j(driver, ticket_ids, labels)
                    
                    # Generate cluster information
                    unique_labels = set(labels)
                    if -1 in unique_labels:
                        unique_labels.remove(-1)
                    
                    clusters = []
                    for cluster_id in sorted(unique_labels):
                        summary, sample_titles = generate_cluster_summary(subset_tickets, labels, cluster_id)
                        clusters.append(ClusterInfo(
                            cluster_id=int(cluster_id),
                            ticket_count=int(np.sum(labels == cluster_id)),
                            summary=summary,
                            sample_titles=sample_titles
                        ))
                    
                    total_time = computation_time + query_time
                    
                    result_data = {
                        'subset_size': subset_size,
                        'algorithm': algorithm,
                        'num_clusters': len(clusters),
                        'computation_time_ms': computation_time,
                        'query_time_ms': query_time,
                        'total_time_ms': total_time,
                        'clusters': [c.dict() for c in clusters],
                        'metrics': metrics,
                        'ticket_ids': ticket_ids
                    }
                    
                    results[key] = result_data
                    all_metrics.append({
                        'key': key,
                        'subset_size': subset_size,
                        'algorithm': algorithm,
                        'computation_time_ms': computation_time,
                        'query_time_ms': query_time,
                        'total_time_ms': total_time,
                        'num_clusters': len(clusters),
                        'silhouette_score': metrics.get('silhouette_score', 0),
                        'avg_cluster_size': metrics.get('avg_cluster_size', 0)
                    })
                    print(f"[Clustering Demo] ✓ Completed {key}: {len(clusters)} clusters in {total_time:.2f}ms")
                except Exception as e:
                    print(f"[Clustering Demo] ✗ Error running {key}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Continue with other combinations
                    continue
        
        # Generate summary
        if all_metrics:
            fastest = min(all_metrics, key=lambda x: x['total_time_ms'])
            best_quality = max(all_metrics, key=lambda x: x['silhouette_score'])
            most_clusters = max(all_metrics, key=lambda x: x['num_clusters'])
            
            summary = {
                'total_combinations': len(all_metrics),
                'fastest': fastest['key'],
                'fastest_time_ms': fastest['total_time_ms'],
                'best_quality': best_quality['key'],
                'best_quality_score': best_quality['silhouette_score'],
                'most_clusters': most_clusters['key'],
                'most_clusters_count': most_clusters['num_clusters']
            }
        else:
            summary = {}
        
        return ClusteringResponse(
            query=request.query,
            results=results,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Clustering failed: {str(e)}"
        )
    finally:
        if 'driver' in locals():
            driver.close()


@router.get("/stats")
async def get_clustering_stats():
    """Get statistics about available tickets in Neo4j."""
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # Count total tickets
            query = """
            MATCH (t:Ticket)
            RETURN count(t) AS total_tickets
            """
            result = session.run(query)
            total_tickets = result.single()['total_tickets']
            
            # Count tickets with embeddings (check both property names)
            query = """
            MATCH (t:Ticket)
            WHERE t.embedding_vector IS NOT NULL OR t.embedding IS NOT NULL
            RETURN count(t) AS tickets_with_embeddings
            """
            result = session.run(query)
            tickets_with_embeddings = result.single()['tickets_with_embeddings']
            
            # Get sample categories
            query = """
            MATCH (t:Ticket)
            WHERE t.category IS NOT NULL
            WITH t.category AS category, count(*) AS count
            ORDER BY count DESC
            LIMIT 10
            RETURN collect({category: category, count: count}) AS top_categories
            """
            result = session.run(query)
            top_categories = result.single()['top_categories']
        
        driver.close()
        
        return {
            "total_tickets": total_tickets,
            "tickets_with_embeddings": tickets_with_embeddings,
            "top_categories": top_categories,
            "available_subset_sizes": [100, 500, 1000],
            "available_algorithms": ["kmeans", "agglomerative", "dbscan"]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )

