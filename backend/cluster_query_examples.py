"""
Example queries demonstrating how to use the three clustering strategies in Neo4j.

This script shows:
1. How to query tickets by cluster type
2. Performance differences between cluster types
3. Trade-offs in practice
"""
from neo4j import GraphDatabase
from backend.utils.env import env
import time
from typing import Dict, List, Any


class ClusterQueryExamples:
    """Examples of querying clusters in Neo4j."""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j connection."""
        self.uri = uri or env("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or env("NEO4J_USER", "neo4j")
        self.password = password or env("NEO4J_PASSWORD", "password123")
        self.driver = None
    
    def connect(self):
        """Connect to Neo4j."""
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        self.driver.verify_connectivity()
        print(f"✓ Connected to Neo4j at {self.uri}")
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def query_cluster_type_a(self, limit: int = 10) -> Dict[str, Any]:
        """
        Query Cluster Type A (Coarse) - FASTEST
        
        Returns tickets from the largest clusters.
        Fast because there are only 5 clusters to search.
        """
        print("\n" + "="*70)
        print("QUERYING CLUSTER TYPE A (Coarse) - FASTEST")
        print("="*70)
        
        start_time = time.time()
        
        with self.driver.session() as session:
            query = """
            MATCH (t:Ticket)-[:BELONGS_TO {cluster_type: 'A'}]->(c:Cluster {type: 'A'})
            RETURN c.id AS cluster_id,
                   c.label AS cluster_label,
                   c.granularity_level AS granularity,
                   c.ticket_count AS ticket_count,
                   collect(t.id)[0..$limit] AS sample_tickets,
                   count(t) AS tickets_in_cluster
            ORDER BY c.ticket_count DESC
            LIMIT 5
            """
            
            result = session.run(query, limit=limit)
            clusters = [dict(record) for record in result]
        
        elapsed = time.time() - start_time
        
        print(f"Query time: {elapsed*1000:.2f} ms")
        print(f"Found {len(clusters)} clusters")
        print("\nTop clusters:")
        for cluster in clusters:
            print(f"  {cluster['cluster_id']}: {cluster['ticket_count']} tickets")
            print(f"    Label: {cluster['cluster_label']}")
            print(f"    Sample tickets: {', '.join(cluster['sample_tickets'][:3])}")
        
        return {
            'cluster_type': 'A',
            'query_time_ms': elapsed * 1000,
            'clusters_found': len(clusters),
            'clusters': clusters
        }
    
    def query_cluster_type_b(self, limit: int = 10) -> Dict[str, Any]:
        """
        Query Cluster Type B (Medium) - BALANCED
        
        Returns tickets from medium-sized clusters.
        Balanced performance with better semantic relevance.
        """
        print("\n" + "="*70)
        print("QUERYING CLUSTER TYPE B (Medium) - BALANCED")
        print("="*70)
        
        start_time = time.time()
        
        with self.driver.session() as session:
            query = """
            MATCH (t:Ticket)-[:BELONGS_TO {cluster_type: 'B'}]->(c:Cluster {type: 'B'})
            RETURN c.id AS cluster_id,
                   c.label AS cluster_label,
                   c.granularity_level AS granularity,
                   c.ticket_count AS ticket_count,
                   collect(t.id)[0..$limit] AS sample_tickets,
                   count(t) AS tickets_in_cluster
            ORDER BY c.ticket_count DESC
            LIMIT 10
            """
            
            result = session.run(query, limit=limit)
            clusters = [dict(record) for record in result]
        
        elapsed = time.time() - start_time
        
        print(f"Query time: {elapsed*1000:.2f} ms")
        print(f"Found {len(clusters)} clusters")
        print("\nTop clusters:")
        for cluster in clusters:
            print(f"  {cluster['cluster_id']}: {cluster['ticket_count']} tickets")
            print(f"    Label: {cluster['cluster_label']}")
            print(f"    Sample tickets: {', '.join(cluster['sample_tickets'][:3])}")
        
        return {
            'cluster_type': 'B',
            'query_time_ms': elapsed * 1000,
            'clusters_found': len(clusters),
            'clusters': clusters
        }
    
    def query_cluster_type_c(self, limit: int = 10) -> Dict[str, Any]:
        """
        Query Cluster Type C (Fine-Grained) - HIGHEST QUALITY
        
        Returns tickets from fine-grained clusters.
        Slower but highest semantic relevance.
        """
        print("\n" + "="*70)
        print("QUERYING CLUSTER TYPE C (Fine-Grained) - HIGHEST QUALITY")
        print("="*70)
        
        start_time = time.time()
        
        with self.driver.session() as session:
            query = """
            MATCH (t:Ticket)-[:BELONGS_TO {cluster_type: 'C'}]->(c:Cluster {type: 'C'})
            RETURN c.id AS cluster_id,
                   c.label AS cluster_label,
                   c.granularity_level AS granularity,
                   c.ticket_count AS ticket_count,
                   collect(t.id)[0..$limit] AS sample_tickets,
                   count(t) AS tickets_in_cluster
            ORDER BY c.ticket_count DESC
            LIMIT 20
            """
            
            result = session.run(query, limit=limit)
            clusters = [dict(record) for record in result]
        
        elapsed = time.time() - start_time
        
        print(f"Query time: {elapsed*1000:.2f} ms")
        print(f"Found {len(clusters)} clusters")
        print("\nTop clusters:")
        for cluster in clusters:
            print(f"  {cluster['cluster_id']}: {cluster['ticket_count']} tickets")
            print(f"    Label: {cluster['cluster_label']}")
            print(f"    Sample tickets: {', '.join(cluster['sample_tickets'][:3])}")
        
        return {
            'cluster_type': 'C',
            'query_time_ms': elapsed * 1000,
            'clusters_found': len(clusters),
            'clusters': clusters
        }
    
    def compare_cluster_performance(self):
        """Compare query performance across all three cluster types."""
        print("\n" + "="*70)
        print("CLUSTER PERFORMANCE COMPARISON")
        print("="*70)
        
        results = {}
        
        # Query each cluster type
        results['A'] = self.query_cluster_type_a()
        results['B'] = self.query_cluster_type_b()
        results['C'] = self.query_cluster_type_c()
        
        # Print comparison
        print("\n" + "="*70)
        print("PERFORMANCE SUMMARY")
        print("="*70)
        print(f"Cluster Type A (Coarse):")
        print(f"  Query time: {results['A']['query_time_ms']:.2f} ms")
        print(f"  Clusters found: {results['A']['clusters_found']}")
        print(f"  ✅ FASTEST")
        
        print(f"\nCluster Type B (Medium):")
        print(f"  Query time: {results['B']['query_time_ms']:.2f} ms")
        print(f"  Clusters found: {results['B']['clusters_found']}")
        print(f"  ⚖️  BALANCED")
        
        print(f"\nCluster Type C (Fine-Grained):")
        print(f"  Query time: {results['C']['query_time_ms']:.2f} ms")
        print(f"  Clusters found: {results['C']['clusters_found']}")
        print(f"  ✅ HIGHEST QUALITY (may be slower)")
        
        print("\n" + "="*70)
        print("TRADE-OFFS:")
        print("  Type A: Fast queries, but may return less relevant results")
        print("  Type B: Balanced speed and relevance")
        print("  Type C: Slower queries, but most relevant results")
        print("="*70)
        
        return results
    
    def find_tickets_by_category(self, category: str, cluster_type: str = 'B'):
        """
        Find tickets by category using a specific cluster type.
        
        Demonstrates how cluster granularity affects search results.
        """
        print(f"\n{'='*70}")
        print(f"FINDING TICKETS BY CATEGORY: '{category}'")
        print(f"Using Cluster Type: {cluster_type}")
        print("="*70)
        
        start_time = time.time()
        
        with self.driver.session() as session:
            query = """
            MATCH (t:Ticket {category: $category})-[:BELONGS_TO {cluster_type: $cluster_type}]->(c:Cluster)
            WHERE c.type = $cluster_type
            RETURN c.id AS cluster_id,
                   c.label AS cluster_label,
                   c.dominant_category AS dominant_category,
                   collect(t.id) AS ticket_ids,
                   count(t) AS ticket_count
            ORDER BY ticket_count DESC
            LIMIT 10
            """
            
            result = session.run(query, category=category, cluster_type=cluster_type)
            clusters = [dict(record) for record in result]
        
        elapsed = time.time() - start_time
        
        print(f"Query time: {elapsed*1000:.2f} ms")
        print(f"Found {len(clusters)} clusters containing '{category}' tickets")
        
        for cluster in clusters:
            print(f"\n  Cluster: {cluster['cluster_id']}")
            print(f"    Label: {cluster['cluster_label']}")
            print(f"    Tickets: {cluster['ticket_count']}")
            print(f"    Sample IDs: {', '.join(cluster['ticket_ids'][:5])}")
        
        return clusters


def main():
    """Run example queries."""
    examples = ClusterQueryExamples()
    
    try:
        examples.connect()
        
        # Compare all cluster types
        examples.compare_cluster_performance()
        
        # Example: Find login issues using different cluster types
        print("\n\n" + "="*70)
        print("EXAMPLE: Finding 'login issue' tickets")
        print("="*70)
        
        for cluster_type in ['A', 'B', 'C']:
            examples.find_tickets_by_category('login issue', cluster_type)
    
    finally:
        examples.close()


if __name__ == "__main__":
    main()



