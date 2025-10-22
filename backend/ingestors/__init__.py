"""Data ingestion modules for CSV and JSONL ticket data."""
from typing import Optional
from backend.ingestors.load_csv import ingest_csv
from backend.ingestors.load_jsonl import ingest_jsonl
from backend.graph.build_graph import Neo4jGraph, connect_similar_tickets
from backend.graph.community import CommunityDetector
from backend.retrieval.vector_store import VectorStore
from backend.utils.env import env


def ingest_all(
    csv_path: Optional[str] = None,
    jsonl_path: Optional[str] = None,
    similarity_threshold: float = 0.7,
    similarity_top_k: int = 10,
    community_algorithm: str = 'louvain'
) -> dict:
    """
    Complete ingestion pipeline.
    
    Steps:
    1. Set up Neo4j constraints
    2. Load CSV data (if path provided)
    3. Load JSONL data (if path provided)
    4. Build inter-ticket similarity edges using embeddings
    5. Run community detection and store communityId
    
    Args:
        csv_path: Path to CSV file (default from env CSV_PATH)
        jsonl_path: Path to JSONL file (default from env JSONL_PATH)
        similarity_threshold: Minimum cosine similarity for edges (0-1)
        similarity_top_k: Max connections per ticket
        community_algorithm: 'louvain' or 'leiden'
    
    Returns:
        Dictionary with ingestion statistics
    """
    print("="*70)
    print("STARTING COMPLETE INGESTION PIPELINE")
    print("="*70)
    
    stats = {
        'csv_tickets': 0,
        'csv_sections': 0,
        'jsonl_tickets': 0,
        'jsonl_sections': 0,
        'total_tickets': 0,
        'total_sections': 0,
        'similarity_edges': 0,
        'communities': 0
    }
    
    # Step 1: Setup constraints
    print("\n[1/5] Setting up Neo4j constraints...")
    with Neo4jGraph() as graph:
        graph.setup_constraints()
        print("✓ Database schema ready")
    
    # Step 2: Load CSV
    csv_path = csv_path or env("CSV_PATH", "/mnt/data/jira_issues_clean.csv")
    try:
        print(f"\n[2/5] Loading CSV from {csv_path}...")
        csv_stats = ingest_csv(csv_path)
        stats['csv_tickets'] = csv_stats['tickets_loaded']
        stats['csv_sections'] = csv_stats['sections_loaded']
        print(f"✓ CSV loaded: {csv_stats['tickets_loaded']} tickets, "
              f"{csv_stats['sections_loaded']} sections")
    except FileNotFoundError:
        print(f"⚠ CSV file not found: {csv_path} (skipping)")
    except Exception as e:
        print(f"⚠ CSV loading failed: {e} (skipping)")
    
    # Step 3: Load JSONL
    jsonl_path = jsonl_path or env("JSONL_PATH", "/mnt/data/jira_issues_rag.jsonl")
    try:
        print(f"\n[3/5] Loading JSONL from {jsonl_path}...")
        jsonl_stats = ingest_jsonl(jsonl_path)
        stats['jsonl_tickets'] = jsonl_stats['tickets_loaded']
        stats['jsonl_sections'] = jsonl_stats['sections_loaded']
        print(f"✓ JSONL loaded: {jsonl_stats['tickets_loaded']} tickets, "
              f"{jsonl_stats['sections_loaded']} sections")
    except FileNotFoundError:
        print(f"⚠ JSONL file not found: {jsonl_path} (skipping)")
    except Exception as e:
        print(f"⚠ JSONL loading failed: {e} (skipping)")
    
    # Calculate totals
    stats['total_tickets'] = stats['csv_tickets'] + stats['jsonl_tickets']
    stats['total_sections'] = stats['csv_sections'] + stats['jsonl_sections']
    
    if stats['total_tickets'] == 0:
        print("\n✗ No tickets loaded. Aborting pipeline.")
        return stats
    
    # Step 4: Build similarity edges
    print(f"\n[4/5] Building similarity edges...")
    print(f"  Threshold: {similarity_threshold}, Top-K: {similarity_top_k}")
    
    try:
        # Load vector store with embeddings
        vector_store = VectorStore()
        vector_store.load()
        
        # Get all unique ticket IDs from vector store metadata
        ticket_embeddings = {}
        
        # Aggregate embeddings per ticket (average of section embeddings)
        print("  Computing ticket embeddings from sections...")
        ticket_sections = {}
        for i, metadata in enumerate(vector_store.metadatas):
            ticket_id = metadata.get('ticket_id')
            if ticket_id:
                if ticket_id not in ticket_sections:
                    ticket_sections[ticket_id] = []
                ticket_sections[ticket_id].append(i)
        
        # Average section embeddings for each ticket
        import numpy as np
        for ticket_id, indices in ticket_sections.items():
            section_embeddings = [vector_store.vectors[i] for i in indices]
            # Average and L2 normalize
            avg_embedding = np.mean(section_embeddings, axis=0)
            avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
            ticket_embeddings[ticket_id] = avg_embedding
        
        print(f"  Generated embeddings for {len(ticket_embeddings)} tickets")
        
        # Create similarity edges
        with Neo4jGraph() as graph:
            edge_count = connect_similar_tickets(
                graph,
                ticket_embeddings,
                threshold=similarity_threshold,
                top_k=similarity_top_k
            )
            stats['similarity_edges'] = edge_count
            print(f"✓ Created {edge_count} similarity edges")
    
    except Exception as e:
        print(f"⚠ Similarity edge creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Run community detection
    print(f"\n[5/5] Running {community_algorithm.upper()} community detection...")
    
    try:
        with Neo4jGraph() as graph:
            detector = CommunityDetector(graph)
            
            # Run algorithm
            if community_algorithm.lower() == 'leiden':
                result = detector.run_leiden(write=True)
            else:
                result = detector.run_louvain(write=True)
            
            stats['communities'] = result.get('communityCount', 0)
            print(f"✓ Detected {stats['communities']} communities")
            print(f"  Modularity: {result.get('modularity', 'N/A')}")
            
            # Get community stats
            comm_stats = detector.get_community_stats()
            print(f"  Average size: {comm_stats['avg_size']:.1f}")
            print(f"  Largest: {comm_stats['largest_size']}, Smallest: {comm_stats['smallest_size']}")
    
    except Exception as e:
        print(f"⚠ Community detection failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("INGESTION PIPELINE COMPLETE")
    print("="*70)
    print(f"Total tickets loaded: {stats['total_tickets']}")
    print(f"Total sections loaded: {stats['total_sections']}")
    print(f"Similarity edges created: {stats['similarity_edges']}")
    print(f"Communities detected: {stats['communities']}")
    print("="*70)
    
    return stats

