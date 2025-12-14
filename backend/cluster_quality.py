"""
Cluster Quality Scoring

Computes and stores cluster quality metrics:
- Intra-cluster similarity (homogeneity)
- Inter-cluster distance (separation)
- Overall quality score
"""
import numpy as np
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from backend.utils.env import env
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import pdist, squareform


class ClusterQualityScorer:
    """
    Compute quality metrics for clusters.
    
    Metrics:
    - Intra-cluster similarity: Average similarity within clusters (higher = better)
    - Inter-cluster distance: Average distance between cluster centroids (higher = better)
    - Quality score: Overall assessment (low/medium/high)
    """
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
        """Initialize Neo4j connection."""
        self.uri = neo4j_uri or env("NEO4J_URI", "bolt://localhost:7687")
        self.user = neo4j_user or env("NEO4J_USER", "neo4j")
        self.password = neo4j_password or env("NEO4J_PASSWORD", "password123")
        self.driver = None
    
    def connect(self):
        """Connect to Neo4j."""
        if self.driver is None:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def compute_intra_cluster_similarity(
        self,
        cluster_type: str,
        sample_size: int = 100
    ) -> float:
        """
        Compute average similarity within clusters (homogeneity).
        
        For each cluster, compute average pairwise similarity of tickets.
        Then average across all clusters.
        
        Args:
            cluster_type: "A", "B", or "C"
            sample_size: Maximum tickets per cluster to sample (for performance)
            
        Returns:
            Average intra-cluster similarity (0.0-1.0)
        """
        with self.driver.session() as session:
            query = """
            MATCH (c:Cluster {type: $cluster_type})<-[:BELONGS_TO {cluster_type: $cluster_type}]-(t:Ticket)
            WHERE t.embedding_vector IS NOT NULL
            WITH c, collect(t)[0..$sample_size] AS tickets
            WHERE size(tickets) > 1
            RETURN c.id AS cluster_id, tickets
            """
            
            result = session.run(query, cluster_type=cluster_type, sample_size=sample_size)
            
            intra_similarities = []
            
            for record in result:
                tickets = record['tickets']
                if len(tickets) < 2:
                    continue
                
                # Get embeddings
                embeddings = np.array([t['embedding_vector'] for t in tickets])
                
                # Compute pairwise similarities
                similarities = cosine_similarity(embeddings)
                
                # Get upper triangle (excluding diagonal)
                n = len(similarities)
                upper_triangle = similarities[np.triu_indices(n, k=1)]
                
                # Average similarity within this cluster
                cluster_avg = float(np.mean(upper_triangle))
                intra_similarities.append(cluster_avg)
            
            # Average across all clusters
            if intra_similarities:
                return float(np.mean(intra_similarities))
            else:
                return 0.0
    
    def compute_inter_cluster_distance(self, cluster_type: str) -> float:
        """
        Compute average distance between cluster centroids (separation).
        
        Args:
            cluster_type: "A", "B", or "C"
            
        Returns:
            Average inter-cluster distance (0.0-2.0, higher = better separation)
        """
        with self.driver.session() as session:
            query = """
            MATCH (c:Cluster {type: $cluster_type})
            WHERE c.centroid IS NOT NULL
            RETURN c.id AS cluster_id, c.centroid AS centroid
            ORDER BY c.id
            """
            
            result = session.run(query, cluster_type=cluster_type)
            centroids = []
            
            for record in result:
                centroids.append(np.array(record['centroid']))
            
            if len(centroids) < 2:
                return 0.0
            
            # Compute pairwise distances
            centroids_array = np.array(centroids)
            
            # Cosine distance = 1 - cosine similarity
            # For normalized vectors, cosine distance ranges from 0 to 2
            distances = pdist(centroids_array, metric='cosine')
            
            # Average inter-cluster distance
            return float(np.mean(distances))
    
    def compute_quality_score(
        self,
        intra_similarity: float,
        inter_distance: float
    ) -> str:
        """
        Compute overall quality score based on metrics.
        
        Args:
            intra_similarity: Intra-cluster similarity (0.0-1.0)
            inter_distance: Inter-cluster distance (0.0-2.0)
            
        Returns:
            Quality score: "low", "medium", or "high"
        """
        # Normalize inter_distance to 0-1 scale (divide by 2)
        normalized_inter = inter_distance / 2.0
        
        # Combined score (weighted average)
        # Higher intra_similarity = better homogeneity
        # Higher inter_distance = better separation
        combined_score = (intra_similarity * 0.6) + (normalized_inter * 0.4)
        
        if combined_score >= 0.75:
            return "high"
        elif combined_score >= 0.55:
            return "medium"
        else:
            return "low"
    
    def score_cluster_type(self, cluster_type: str) -> Dict[str, Any]:
        """
        Compute all quality metrics for a cluster type.
        
        Args:
            cluster_type: "A", "B", or "C"
            
        Returns:
            Dictionary with quality metrics
        """
        print(f"Computing quality metrics for Cluster Type {cluster_type}...")
        
        intra_similarity = self.compute_intra_cluster_similarity(cluster_type)
        inter_distance = self.compute_inter_cluster_distance(cluster_type)
        quality_score = self.compute_quality_score(intra_similarity, inter_distance)
        
        print(f"  Intra-cluster similarity: {intra_similarity:.3f}")
        print(f"  Inter-cluster distance: {inter_distance:.3f}")
        print(f"  Quality score: {quality_score}")
        
        return {
            'quality_score': quality_score,
            'intra_similarity': round(intra_similarity, 3),
            'inter_distance': round(inter_distance, 3)
        }
    
    def score_all_clusters(self) -> Dict[str, Dict[str, Any]]:
        """
        Compute quality metrics for all cluster types.
        
        Returns:
            Dictionary with metrics for each cluster type
        """
        self.connect()
        
        try:
            results = {}
            
            for cluster_type in ['A', 'B', 'C']:
                results[f'cluster_type_{cluster_type.lower()}'] = self.score_cluster_type(cluster_type)
            
            return results
        
        finally:
            self.close()


def compute_cluster_quality() -> Dict[str, Dict[str, Any]]:
    """
    Simple interface to compute cluster quality metrics.
    
    Returns:
        Dictionary with quality metrics for all cluster types:
        {
            "cluster_type_a": {
                "quality_score": "low",
                "intra_similarity": 0.60,
                "inter_distance": 0.45
            },
            ...
        }
    """
    scorer = ClusterQualityScorer()
    return scorer.score_all_clusters()



