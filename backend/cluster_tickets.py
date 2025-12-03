"""
Three Clustering Strategies for Support Tickets

This module implements three distinct clustering strategies with different
trade-offs between speed and semantic relevance.

MODULE STRUCTURE:
- Data Loading: Load tickets and generate embeddings
- Clustering Functions: Three strategies (A, B, C)
- Metadata Generation: Create cluster metadata and assignments
- Output: Save clusters to JSON for Neo4j ingestion

EXTENSION POINTS:
- Add new clustering algorithm: Create new function following pattern
- Modify cluster count: Change k or n_clusters parameters
- Add custom metadata: Extend ClusterMetadata class

MOCKED COMPONENTS:
- Embeddings: Can use MockEmbedding if real model unavailable
  (see embedding_interface.py for details)

CLUSTER TYPE A (Coarse / Low-Quality):
- Algorithm: K-Means with k=5
- Characteristics: Very few large clusters (5 clusters)
- Speed: Fastest (O(n*k*d) where k=5)
- Quality: Lower semantic relevance, coarse groupings
- Use Case: Quick filtering, large-scale searches, initial exploration
- Trade-off: Optimized for speed, sacrifices semantic precision

CLUSTER TYPE B (Medium / Balanced):
- Algorithm: K-Means with k=20
- Characteristics: Moderate number of clusters (20 clusters)
- Speed: Moderate (O(n*k*d) where k=20)
- Quality: Balanced semantic relevance
- Use Case: General purpose, production use, balanced performance
- Trade-off: Balanced between speed and quality

CLUSTER TYPE C (Fine-Grained / High-Quality):
- Algorithm: Agglomerative Clustering with n_clusters=100
- Characteristics: Many small, fine-grained clusters (100 clusters)
- Speed: Slowest (O(n^2*d) for hierarchical clustering)
- Quality: Highest semantic relevance, precise groupings
- Use Case: Precise searches, high accuracy requirements, detailed analysis
- Trade-off: Optimized for quality, sacrifices speed

Neo4j Storage:
- Each cluster is stored as a (:Cluster) node with:
  - id: Unique identifier (e.g., "A_cluster_0")
  - type: "A", "B", or "C"
  - label: Human-readable label
  - granularity_level: "coarse", "medium", or "fine"
  - ticket_count: Number of tickets in cluster
  - dominant_category: Most common category
  - categories: List of all categories
  - centroid: 768-dimensional embedding vector

- Tickets are linked via (:Ticket)-[:BELONGS_TO]->(:Cluster) relationships
"""
import json
import numpy as np
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sentence_transformers import SentenceTransformer
import argparse
from tqdm import tqdm


def load_tickets(jsonl_path: str) -> List[Dict[str, Any]]:
    """Load tickets from JSONL file."""
    tickets = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            tickets.append(json.loads(line.strip()))
    return tickets


def generate_embeddings(tickets: List[Dict[str, Any]], batch_size: int = 32) -> np.ndarray:
    """Generate embeddings for all tickets."""
    print("Loading embedding model...")
    
    # Try correct model identifier first
    model_name = None
    try:
        model_name = 'intfloat/e5-base-v2'
        print(f"Attempting to load: {model_name}")
        model = SentenceTransformer(model_name)
        print(f"✓ Successfully loaded: {model_name}")
    except Exception as e:
        print(f"✗ Failed to load {model_name}: {e}")
        # Try alternative model
        try:
            model_name = 'sentence-transformers/all-MiniLM-L6-v2'
            print(f"Attempting fallback model: {model_name}")
            model = SentenceTransformer(model_name)
            print(f"✓ Successfully loaded fallback: {model_name}")
        except Exception as e2:
            print(f"✗ Fallback model also failed: {e2}")
            raise RuntimeError(
                "Could not load any embedding model. "
                "Please check your internet connection or use mock embeddings."
            ) from e2
    
    print("Generating embeddings...")
    texts = [f"{t['title']} {t['description']}" for t in tickets]
    
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        embeddings.append(batch_embeddings)
    
    return np.vstack(embeddings)


def cluster_type_a_coarse(embeddings: np.ndarray, num_clusters: int = 5) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    CLUSTER TYPE A: Coarse / Low-Quality Clusters
    
    Algorithm: K-Means clustering
    Parameters:
        - n_clusters: 5 (very few clusters)
        - n_init: 10 (multiple initializations for stability)
        - random_state: 42 (reproducibility)
    
    Characteristics:
        - Very few large clusters (typically 5)
        - Fast computation: O(n*k*d) where k=5
        - Lower semantic relevance due to coarse groupings
        - Large variance within clusters
    
    Trade-offs:
        ✅ FASTEST: ~1-5 seconds for 5000 tickets
        ✅ Low memory usage
        ✅ Good for initial exploration
        ❌ Lower semantic precision
        ❌ Large clusters may mix unrelated topics
        ❌ Less useful for precise similarity search
    
    Returns:
        labels: Cluster assignments for each ticket
        metrics: Performance metrics (timing, quality scores)
    """
    print(f"\n{'='*70}")
    print(f"CLUSTER TYPE A: Coarse Clustering (k={num_clusters})")
    print(f"{'='*70}")
    print("Algorithm: K-Means")
    print("Characteristics: Very few large clusters, optimized for speed")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    # K-Means with small k for fast, coarse clustering
    kmeans = KMeans(
        n_clusters=num_clusters,
        random_state=42,
        n_init=10,  # Multiple initializations
        max_iter=300,
        algorithm='lloyd'  # Standard K-Means
    )
    
    print("Running K-Means clustering...")
    labels = kmeans.fit_predict(embeddings)
    
    elapsed_time = time.time() - start_time
    
    # Calculate quality metrics
    print("Calculating quality metrics...")
    silhouette = silhouette_score(embeddings, labels) if len(set(labels)) > 1 else 0.0
    calinski_harabasz = calinski_harabasz_score(embeddings, labels) if len(set(labels)) > 1 else 0.0
    
    metrics = {
        'algorithm': 'K-Means',
        'num_clusters': num_clusters,
        'computation_time_seconds': elapsed_time,
        'silhouette_score': float(silhouette),
        'calinski_harabasz_score': float(calinski_harabasz),
        'avg_tickets_per_cluster': len(embeddings) / num_clusters
    }
    
    print(f"✓ Completed in {elapsed_time:.2f} seconds")
    print(f"  Silhouette score: {silhouette:.3f}")
    print(f"  Average tickets per cluster: {metrics['avg_tickets_per_cluster']:.1f}")
    
    return labels, metrics


def cluster_type_b_medium(embeddings: np.ndarray, num_clusters: int = 20) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    CLUSTER TYPE B: Medium / Balanced Clusters
    
    Algorithm: K-Means clustering
    Parameters:
        - n_clusters: 20 (moderate number of clusters)
        - n_init: 10 (multiple initializations for stability)
        - random_state: 42 (reproducibility)
    
    Characteristics:
        - Moderate number of clusters (typically 20)
        - Balanced computation: O(n*k*d) where k=20
        - Balanced semantic relevance
        - Good trade-off between speed and quality
    
    Trade-offs:
        ✅ MODERATE SPEED: ~5-15 seconds for 5000 tickets
        ✅ Balanced semantic precision
        ✅ Good for production use
        ✅ Reasonable memory usage
        ⚠️  Moderate cluster sizes
        ⚠️  Some mixing of related but distinct topics
    
    Returns:
        labels: Cluster assignments for each ticket
        metrics: Performance metrics (timing, quality scores)
    """
    print(f"\n{'='*70}")
    print(f"CLUSTER TYPE B: Medium Clustering (k={num_clusters})")
    print(f"{'='*70}")
    print("Algorithm: K-Means")
    print("Characteristics: Moderate clusters, balanced speed and quality")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    # K-Means with moderate k for balanced clustering
    kmeans = KMeans(
        n_clusters=num_clusters,
        random_state=42,
        n_init=10,
        max_iter=300,
        algorithm='lloyd'
    )
    
    print("Running K-Means clustering...")
    labels = kmeans.fit_predict(embeddings)
    
    elapsed_time = time.time() - start_time
    
    # Calculate quality metrics
    print("Calculating quality metrics...")
    silhouette = silhouette_score(embeddings, labels) if len(set(labels)) > 1 else 0.0
    calinski_harabasz = calinski_harabasz_score(embeddings, labels) if len(set(labels)) > 1 else 0.0
    
    metrics = {
        'algorithm': 'K-Means',
        'num_clusters': num_clusters,
        'computation_time_seconds': elapsed_time,
        'silhouette_score': float(silhouette),
        'calinski_harabasz_score': float(calinski_harabasz),
        'avg_tickets_per_cluster': len(embeddings) / num_clusters
    }
    
    print(f"✓ Completed in {elapsed_time:.2f} seconds")
    print(f"  Silhouette score: {silhouette:.3f}")
    print(f"  Average tickets per cluster: {metrics['avg_tickets_per_cluster']:.1f}")
    
    return labels, metrics


def cluster_type_c_fine(embeddings: np.ndarray, num_clusters: int = 100) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    CLUSTER TYPE C: Fine-Grained / High-Quality Clusters
    
    Algorithm: Agglomerative Hierarchical Clustering
    Parameters:
        - n_clusters: 100 (many small clusters)
        - linkage: 'average' (average linkage for balanced clusters)
        - metric: 'cosine' (cosine similarity for embeddings)
    
    Characteristics:
        - Many small, fine-grained clusters (typically 100)
        - Slower computation: O(n^2*d) for hierarchical clustering
        - Highest semantic relevance
        - Precise groupings with low variance within clusters
    
    Trade-offs:
        ✅ HIGHEST QUALITY: Best semantic precision
        ✅ Small, focused clusters
        ✅ Excellent for precise similarity search
        ✅ Low variance within clusters
        ❌ SLOWEST: ~30-120 seconds for 5000 tickets
        ❌ Higher memory usage
        ❌ O(n^2) complexity limits scalability
    
    Returns:
        labels: Cluster assignments for each ticket
        metrics: Performance metrics (timing, quality scores)
    """
    print(f"\n{'='*70}")
    print(f"CLUSTER TYPE C: Fine-Grained Clustering (k={num_clusters})")
    print(f"{'='*70}")
    print("Algorithm: Agglomerative Hierarchical Clustering")
    print("Characteristics: Many small clusters, optimized for quality")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    # Agglomerative clustering for high-quality, fine-grained clusters
    # Note: This is computationally expensive but produces better clusters
    print("Running Agglomerative Clustering (this may take a while)...")
    clustering = AgglomerativeClustering(
        n_clusters=num_clusters,
        linkage='average',  # Average linkage for balanced clusters
        metric='cosine',    # Cosine similarity for normalized embeddings
        compute_full_tree=False  # Don't compute full tree (faster)
    )
    
    labels = clustering.fit_predict(embeddings)
    
    elapsed_time = time.time() - start_time
    
    # Calculate quality metrics
    print("Calculating quality metrics...")
    silhouette = silhouette_score(embeddings, labels) if len(set(labels)) > 1 else 0.0
    calinski_harabasz = calinski_harabasz_score(embeddings, labels) if len(set(labels)) > 1 else 0.0
    
    metrics = {
        'algorithm': 'Agglomerative Clustering',
        'num_clusters': num_clusters,
        'computation_time_seconds': elapsed_time,
        'silhouette_score': float(silhouette),
        'calinski_harabasz_score': float(calinski_harabasz),
        'avg_tickets_per_cluster': len(embeddings) / num_clusters
    }
    
    print(f"✓ Completed in {elapsed_time:.2f} seconds")
    print(f"  Silhouette score: {silhouette:.3f}")
    print(f"  Average tickets per cluster: {metrics['avg_tickets_per_cluster']:.1f}")
    
    return labels, metrics


def create_cluster_metadata(
    tickets: List[Dict[str, Any]],
    embeddings: np.ndarray,
    labels: np.ndarray,
    cluster_type: str,
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create cluster metadata for Neo4j storage.
    
    Each cluster node will have:
    - id: Unique identifier (e.g., "A_cluster_0")
    - type: "A", "B", or "C"
    - label: Human-readable label based on dominant category
    - granularity_level: "coarse", "medium", or "fine"
    - ticket_count: Number of tickets in cluster
    - dominant_category: Most common category
    - categories: List of all categories in cluster
    - centroid: 768-dimensional embedding vector (mean of cluster embeddings)
    
    Args:
        tickets: List of ticket dictionaries
        embeddings: Embedding vectors (n_tickets x 768)
        labels: Cluster assignments (n_tickets,)
        cluster_type: "A", "B", or "C"
        metrics: Performance metrics from clustering
    
    Returns:
        Dictionary with cluster metadata ready for Neo4j ingestion
    """
    num_clusters = len(set(labels))
    
    # Map cluster type to granularity level
    granularity_map = {
        'A': 'coarse',
        'B': 'medium',
        'C': 'fine'
    }
    granularity = granularity_map.get(cluster_type, 'medium')
    
    clusters = {}
    for cluster_id in range(num_clusters):
        cluster_indices = np.where(labels == cluster_id)[0]
        cluster_tickets = [tickets[i] for i in cluster_indices]
        cluster_embeddings = embeddings[cluster_indices]
        
        # Calculate centroid (mean embedding vector)
        centroid = np.mean(cluster_embeddings, axis=0)
        
        # Get category statistics
        categories = [t['category'] for t in cluster_tickets]
        most_common_category = max(set(categories), key=categories.count) if categories else "unknown"
        unique_categories = list(set(categories))
        
        # Generate human-readable label
        label = f"{most_common_category.replace('_', ' ').title()} Cluster"
        
        # Create cluster metadata matching Neo4j schema
        cluster_key = f"{cluster_type}_cluster_{cluster_id}"
        clusters[cluster_key] = {
            "id": cluster_key,  # Neo4j node id
            "cluster_id": cluster_id,  # Numeric cluster ID
            "type": cluster_type,
            "label": label,
            "granularity_level": granularity,
            "ticket_count": len(cluster_tickets),
            "ticket_ids": [t['id'] for t in cluster_tickets],
            "centroid": centroid.tolist(),  # 768-dimensional vector
            "dominant_category": most_common_category,
            "categories": unique_categories
        }
    
    return {
        "cluster_type": cluster_type,
        "granularity_level": granularity,
        "num_clusters": num_clusters,
        "clusters": clusters,
        "labels": labels.tolist(),
        "metrics": metrics  # Include performance metrics
    }


def save_clustering_results(
    tickets: List[Dict[str, Any]],
    embeddings: np.ndarray,
    output_dir: str
) -> None:
    """Generate and save all three clustering strategies."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate embeddings if not provided
    if embeddings is None:
        embeddings = generate_embeddings(tickets)
    
    # Save embeddings
    print("\nSaving embeddings...")
    np.save(output_path / "ticket_embeddings.npy", embeddings)
    
    # Create cluster assignments
    print("\n" + "=" * 70)
    print("CREATING THREE CLUSTERING STRATEGIES")
    print("=" * 70)
    print("\nEach strategy uses different algorithms and parameters:")
    print("  Type A: K-Means (k=5)   → Fast, coarse clusters")
    print("  Type B: K-Means (k=20)  → Balanced speed and quality")
    print("  Type C: Agglomerative (k=100) → Slow, fine-grained clusters")
    print("=" * 70)
    
    # Cluster Type A: Coarse (5 clusters) - FASTEST
    labels_a, metrics_a = cluster_type_a_coarse(embeddings, num_clusters=5)
    metadata_a = create_cluster_metadata(tickets, embeddings, labels_a, "A", metrics_a)
    
    # Cluster Type B: Medium (20 clusters) - BALANCED
    labels_b, metrics_b = cluster_type_b_medium(embeddings, num_clusters=20)
    metadata_b = create_cluster_metadata(tickets, embeddings, labels_b, "B", metrics_b)
    
    # Cluster Type C: Fine-grained (100 clusters) - HIGHEST QUALITY
    labels_c, metrics_c = cluster_type_c_fine(embeddings, num_clusters=100)
    metadata_c = create_cluster_metadata(tickets, embeddings, labels_c, "C", metrics_c)
    
    # Add cluster assignments to tickets
    tickets_with_clusters = []
    for i, ticket in enumerate(tickets):
        ticket_copy = ticket.copy()
        ticket_copy['embedding'] = embeddings[i].tolist()
        ticket_copy['cluster_A'] = int(labels_a[i])
        ticket_copy['cluster_B'] = int(labels_b[i])
        ticket_copy['cluster_C'] = int(labels_c[i])
        tickets_with_clusters.append(ticket_copy)
    
    # Save results
    print("\nSaving clustering results...")
    
    # Save tickets with cluster assignments
    with open(output_path / "tickets_with_clusters.jsonl", 'w', encoding='utf-8') as f:
        for ticket in tickets_with_clusters:
            f.write(json.dumps(ticket, ensure_ascii=False) + '\n')
    
    # Save cluster metadata
    with open(output_path / "cluster_metadata_A.json", 'w', encoding='utf-8') as f:
        json.dump(metadata_a, f, indent=2, ensure_ascii=False)
    
    with open(output_path / "cluster_metadata_B.json", 'w', encoding='utf-8') as f:
        json.dump(metadata_b, f, indent=2, ensure_ascii=False)
    
    with open(output_path / "cluster_metadata_C.json", 'w', encoding='utf-8') as f:
        json.dump(metadata_c, f, indent=2, ensure_ascii=False)
    
    # Print comprehensive summary with trade-offs
    print("\n" + "=" * 70)
    print("CLUSTERING COMPLETE - SUMMARY & TRADE-OFFS")
    print("=" * 70)
    
    print(f"\nCLUSTER TYPE A (Coarse / Low-Quality):")
    print(f"  Algorithm: {metadata_a['metrics']['algorithm']}")
    print(f"  Number of clusters: {metadata_a['num_clusters']}")
    print(f"  Computation time: {metadata_a['metrics']['computation_time_seconds']:.2f} seconds")
    print(f"  Average tickets per cluster: {metadata_a['metrics']['avg_tickets_per_cluster']:.1f}")
    print(f"  Silhouette score: {metadata_a['metrics']['silhouette_score']:.3f}")
    print(f"  ✅ FASTEST - Optimized for speed")
    print(f"  ❌ Lower semantic precision")
    
    print(f"\nCLUSTER TYPE B (Medium / Balanced):")
    print(f"  Algorithm: {metadata_b['metrics']['algorithm']}")
    print(f"  Number of clusters: {metadata_b['num_clusters']}")
    print(f"  Computation time: {metadata_b['metrics']['computation_time_seconds']:.2f} seconds")
    print(f"  Average tickets per cluster: {metadata_b['metrics']['avg_tickets_per_cluster']:.1f}")
    print(f"  Silhouette score: {metadata_b['metrics']['silhouette_score']:.3f}")
    print(f"  ⚖️  BALANCED - Good trade-off between speed and quality")
    
    print(f"\nCLUSTER TYPE C (Fine-Grained / High-Quality):")
    print(f"  Algorithm: {metadata_c['metrics']['algorithm']}")
    print(f"  Number of clusters: {metadata_c['num_clusters']}")
    print(f"  Computation time: {metadata_c['metrics']['computation_time_seconds']:.2f} seconds")
    print(f"  Average tickets per cluster: {metadata_c['metrics']['avg_tickets_per_cluster']:.1f}")
    print(f"  Silhouette score: {metadata_c['metrics']['silhouette_score']:.3f}")
    print(f"  ✅ HIGHEST QUALITY - Best semantic precision")
    print(f"  ❌ SLOWEST - Optimized for quality")
    
    print(f"\n{'='*70}")
    print("NEO4J STORAGE INFORMATION")
    print(f"{'='*70}")
    print("Cluster nodes will be created with:")
    print("  - id: Unique identifier (e.g., 'A_cluster_0')")
    print("  - type: 'A', 'B', or 'C'")
    print("  - label: Human-readable label")
    print("  - granularity_level: 'coarse', 'medium', or 'fine'")
    print("  - ticket_count: Number of tickets")
    print("  - dominant_category: Most common category")
    print("  - categories: List of all categories")
    print("  - centroid: 768-dimensional embedding vector")
    print("\nTickets will be linked via:")
    print("  (:Ticket)-[:BELONGS_TO {cluster_type, assigned_at, similarity_score}]->(:Cluster)")
    
    print(f"\nResults saved to: {output_path}")
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create three clustering strategies for support tickets"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="./mnt/data/support_tickets.jsonl",
        help="Input JSONL file with tickets (default: ./mnt/data/support_tickets.jsonl)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./mnt/data/clusters",
        help="Output directory for clustering results (default: ./mnt/data/clusters)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TICKET CLUSTERING SYSTEM")
    print("=" * 70)
    print(f"Input file: {args.input}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 70)
    print()
    
    # Load tickets
    print("Loading tickets...")
    tickets = load_tickets(args.input)
    print(f"Loaded {len(tickets)} tickets")
    
    # Generate embeddings
    embeddings = generate_embeddings(tickets)
    
    # Create and save clustering results
    save_clustering_results(tickets, embeddings, args.output_dir)


if __name__ == "__main__":
    main()

