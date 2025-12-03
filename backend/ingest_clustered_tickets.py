"""
Ingest clustered tickets into Neo4j.

Creates:
- Ticket nodes with embeddings
- Cluster nodes (3 types: A, B, C)
- BELONGS_TO relationships
"""
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from neo4j import GraphDatabase
from backend.utils.env import env
import argparse
from tqdm import tqdm


class Neo4jClusterIngester:
    """Ingest tickets and clusters into Neo4j."""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j connection."""
        self.uri = uri or env("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or env("NEO4J_USER", "neo4j")
        self.password = password or env("NEO4J_PASSWORD", "password123")
        self.driver = None
    
    def connect(self):
        """Connect to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            print(f"✓ Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            print("✓ Neo4j connection closed")
    
    def setup_constraints(self):
        """Create constraints and indexes."""
        print("Setting up constraints and indexes...")
        
        with self.driver.session() as session:
            # Create constraints
            session.run("CREATE CONSTRAINT ticket_id_unique IF NOT EXISTS FOR (t:Ticket) REQUIRE t.id IS UNIQUE")
            session.run("CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (c:Cluster) REQUIRE c.id IS UNIQUE")
            
            # Create indexes for tickets
            session.run("CREATE INDEX ticket_category IF NOT EXISTS FOR (t:Ticket) ON (t.category)")
            session.run("CREATE INDEX ticket_priority IF NOT EXISTS FOR (t:Ticket) ON (t.priority)")
            session.run("CREATE INDEX ticket_status IF NOT EXISTS FOR (t:Ticket) ON (t.status)")
            session.run("CREATE INDEX ticket_created_at IF NOT EXISTS FOR (t:Ticket) ON (t.created_at)")
            
            # Create indexes for clusters
            session.run("CREATE INDEX cluster_type IF NOT EXISTS FOR (c:Cluster) ON (c.type)")
            session.run("CREATE INDEX cluster_granularity IF NOT EXISTS FOR (c:Cluster) ON (c.granularity_level)")
            session.run("CREATE INDEX cluster_type_granularity IF NOT EXISTS FOR (c:Cluster) ON (c.type, c.granularity_level)")
            
            print("✓ Constraints and indexes created")
    
    def ingest_tickets(self, tickets: List[Dict[str, Any]], batch_size: int = 100):
        """Ingest ticket nodes."""
        print(f"\nIngesting {len(tickets)} tickets...")
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(tickets), batch_size), desc="Tickets"):
                batch = tickets[i:i + batch_size]
                
                query = """
                UNWIND $tickets AS ticket
                MERGE (t:Ticket {id: ticket.id})
                SET t.title = ticket.title,
                    t.description = ticket.description,
                    t.category = ticket.category,
                    t.priority = ticket.priority,
                    t.status = ticket.status,
                    t.created_at = ticket.created_at,
                    t.timestamp = ticket.timestamp,
                    t.embedding_vector = ticket.embedding_vector
                RETURN count(t) AS count
                """
                
                prepared_tickets = []
                for ticket in batch:
                    prepared_tickets.append({
                        'id': ticket['id'],
                        'title': ticket['title'],
                        'description': ticket['description'],
                        'category': ticket['category'],
                        'priority': ticket['priority'],
                        'status': ticket.get('status', 'open'),
                        'created_at': ticket.get('created_at', ticket.get('timestamp', '')),
                        'timestamp': ticket.get('timestamp', ticket.get('created_at', '')),
                        'embedding_vector': ticket.get('embedding', ticket.get('embedding_vector', []))
                    })
                
                session.run(query, tickets=prepared_tickets)
        
        print(f"✓ Ingested {len(tickets)} tickets")
    
    def ingest_clusters(self, cluster_metadata: Dict[str, Any], cluster_type: str):
        """Ingest cluster nodes."""
        clusters = cluster_metadata['clusters']
        print(f"\nIngesting {len(clusters)} {cluster_type} clusters...")
        
        # Map cluster type to granularity level
        granularity_map = {
            'A': 'coarse',
            'B': 'medium',
            'C': 'fine'
        }
        granularity = granularity_map.get(cluster_type, 'medium')
        
        with self.driver.session() as session:
            for cluster_key, cluster_data in tqdm(clusters.items(), desc=f"Clusters {cluster_type}"):
                # Generate cluster label from dominant category
                dominant_cat = cluster_data['dominant_category']
                label = f"{dominant_cat.replace('_', ' ').title()} Cluster"
                
                query = """
                MERGE (c:Cluster {id: $cluster_id})
                SET c.type = $cluster_type,
                    c.label = $label,
                    c.granularity_level = $granularity_level,
                    c.ticket_count = $ticket_count,
                    c.dominant_category = $dominant_category,
                    c.categories = $categories,
                    c.centroid = $centroid
                RETURN c
                """
                
                session.run(query, {
                    'cluster_id': cluster_key,  # Use cluster_key as id
                    'cluster_type': cluster_type,
                    'label': label,
                    'granularity_level': granularity,
                    'ticket_count': cluster_data['ticket_count'],
                    'dominant_category': cluster_data['dominant_category'],
                    'categories': cluster_data['categories'],
                    'centroid': cluster_data['centroid']
                })
        
        print(f"✓ Ingested {len(clusters)} {cluster_type} clusters")
    
    def create_belongs_to_relationships(
        self,
        tickets: List[Dict[str, Any]],
        cluster_type: str,
        batch_size: int = 100
    ):
        """Create BELONGS_TO relationships."""
        print(f"\nCreating BELONGS_TO relationships for cluster type {cluster_type}...")
        
        cluster_field = f'cluster_{cluster_type}'
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(tickets), batch_size), desc=f"Relationships {cluster_type}"):
                batch = tickets[i:i + batch_size]
                
                query = f"""
                UNWIND $pairs AS pair
                MATCH (t:Ticket {{id: pair.ticket_id}})
                MATCH (c:Cluster {{id: pair.cluster_id}})
                MERGE (t)-[r:BELONGS_TO]->(c)
                SET r.cluster_type = $cluster_type,
                    r.assigned_at = datetime(),
                    r.similarity_score = pair.similarity_score
                RETURN count(*) AS count
                """
                
                pairs = []
                for ticket in batch:
                    cluster_id = ticket.get(cluster_field)
                    if cluster_id is not None:
                        cluster_key = f"{cluster_type}_cluster_{cluster_id}"
                        pairs.append({
                            'ticket_id': ticket['id'],
                            'cluster_id': cluster_key,
                            'similarity_score': 0.85  # Default similarity, can be calculated
                        })
                
                if pairs:
                    session.run(query, pairs=pairs, cluster_type=cluster_type)
        
        print(f"✓ Created BELONGS_TO relationships for cluster type {cluster_type}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self.driver.session() as session:
            # Count nodes
            ticket_count = session.run("MATCH (t:Ticket) RETURN count(t) AS count").single()['count']
            cluster_count = session.run("MATCH (c:Cluster) RETURN count(c) AS count").single()['count']
            
            # Count relationships
            rel_count = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS count").single()['count']
            
            # Count by cluster type
            cluster_types = {}
            result = session.run("""
                MATCH (c:Cluster)
                RETURN c.cluster_type AS type, count(c) AS count
            """)
            for record in result:
                cluster_types[record['type']] = record['count']
            
            return {
                'tickets': ticket_count,
                'clusters': cluster_count,
                'relationships': rel_count,
                'cluster_types': cluster_types
            }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest clustered tickets into Neo4j"
    )
    parser.add_argument(
        "--tickets-file",
        type=str,
        default="./mnt/data/clusters/tickets_with_clusters.jsonl",
        help="Input file with tickets and cluster assignments"
    )
    parser.add_argument(
        "--cluster-dir",
        type=str,
        default="./mnt/data/clusters",
        help="Directory with cluster metadata files"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("NEO4J CLUSTER INGESTION")
    print("=" * 70)
    print(f"Tickets file: {args.tickets_file}")
    print(f"Cluster directory: {args.cluster_dir}")
    print("=" * 70)
    print()
    
    # Load tickets
    print("Loading tickets...")
    tickets = []
    with open(args.tickets_file, 'r', encoding='utf-8') as f:
        for line in f:
            tickets.append(json.loads(line.strip()))
    print(f"Loaded {len(tickets)} tickets")
    
    # Load cluster metadata
    cluster_dir = Path(args.cluster_dir)
    print("\nLoading cluster metadata...")
    
    with open(cluster_dir / "cluster_metadata_A.json", 'r') as f:
        metadata_a = json.load(f)
    print(f"Loaded Cluster Type A: {metadata_a['num_clusters']} clusters")
    
    with open(cluster_dir / "cluster_metadata_B.json", 'r') as f:
        metadata_b = json.load(f)
    print(f"Loaded Cluster Type B: {metadata_b['num_clusters']} clusters")
    
    with open(cluster_dir / "cluster_metadata_C.json", 'r') as f:
        metadata_c = json.load(f)
    print(f"Loaded Cluster Type C: {metadata_c['num_clusters']} clusters")
    
    # Ingest into Neo4j
    ingester = Neo4jClusterIngester()
    ingester.connect()
    
    try:
        # Setup constraints
        ingester.setup_constraints()
        
        # Ingest tickets
        ingester.ingest_tickets(tickets)
        
        # Ingest clusters
        ingester.ingest_clusters(metadata_a, "A")
        ingester.ingest_clusters(metadata_b, "B")
        ingester.ingest_clusters(metadata_c, "C")
        
        # Create relationships
        ingester.create_belongs_to_relationships(tickets, "A")
        ingester.create_belongs_to_relationships(tickets, "B")
        ingester.create_belongs_to_relationships(tickets, "C")
        
        # Print statistics
        print("\n" + "=" * 70)
        print("INGESTION COMPLETE")
        print("=" * 70)
        stats = ingester.get_stats()
        print(f"Tickets: {stats['tickets']}")
        print(f"Clusters: {stats['clusters']}")
        print(f"Relationships: {stats['relationships']}")
        print(f"\nClusters by type:")
        for cluster_type, count in stats['cluster_types'].items():
            print(f"  Type {cluster_type}: {count} clusters")
        print("=" * 70)
    
    finally:
        ingester.close()


if __name__ == "__main__":
    main()

