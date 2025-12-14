"""
Example Usage Scripts

This file demonstrates how to use each component of the cluster comparison system.
Run individual examples or use as reference for integration.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def example_1_generate_mock_data():
    """Example: Generate mock support tickets."""
    print("=" * 70)
    print("Example 1: Generate Mock Support Tickets")
    print("=" * 70)
    
    from backend.generate_support_tickets import generate_support_ticket
    
    # Generate a few example tickets
    categories = ["login issue", "billing", "bug", "feature request"]
    
    for i, category in enumerate(categories):
        ticket = generate_support_ticket(i, category)
        print(f"\nTicket {i+1} ({category}):")
        print(f"  ID: {ticket['id']}")
        print(f"  Title: {ticket['title']}")
        print(f"  Priority: {ticket['priority']}")
        print(f"  Status: {ticket['status']}")
        print(f"  Created: {ticket['created_at']}")


def example_2_embedding_interface():
    """Example: Use embedding interface (real or mock)."""
    print("\n" + "=" * 70)
    print("Example 2: Embedding Interface")
    print("=" * 70)
    
    from backend.embedding_interface import SentenceTransformerEmbedding, MockEmbedding
    
    # Try real model first, fall back to mock
    try:
        print("\nAttempting to load real embedding model...")
        model = SentenceTransformerEmbedding()
        print(f"✓ Real model loaded. Dimension: {model.get_sentence_embedding_dimension()}")
    except Exception as e:
        print(f"✗ Real model failed: {e}")
        print("Using mock embedding model...")
        model = MockEmbedding(dimension=768)
        print(f"✓ Mock model initialized. Dimension: {model.get_sentence_embedding_dimension()}")
    
    # Embed a query
    query = "login authentication error"
    embedding = model.embed_query(query)
    print(f"\nQuery: '{query}'")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding sample (first 5 values): {embedding[:5]}")


def example_3_cluster_selection():
    """Example: Smart cluster selection."""
    print("\n" + "=" * 70)
    print("Example 3: Smart Cluster Selection")
    print("=" * 70)
    
    from backend.cluster_selection import select_cluster_strategy
    
    test_queries = [
        "login",  # Short query
        "specific authentication error with OAuth",  # Precision keywords
        "show me all tickets",  # Broad keywords
        "database connection timeout",  # Technical
        "how to fix bug",  # Medium length
    ]
    
    for query in test_queries:
        result = select_cluster_strategy(query)
        print(f"\nQuery: '{query}'")
        print(f"  Selected clusters: {result['selected_clusters']}")
        print(f"  Explanation: {result['explanation']}")
        print(f"  Analysis: {result['analysis']}")


def example_4_relevance_feedback():
    """Example: Relevance feedback system."""
    print("\n" + "=" * 70)
    print("Example 4: Relevance Feedback")
    print("=" * 70)
    
    from backend.relevance_feedback import (
        add_feedback,
        get_cluster_weights,
        get_ticket_boost,
        get_feedback_statistics
    )
    
    # Add some sample feedback
    print("\nAdding feedback...")
    add_feedback("TICKET-10000", "login issue", "A", True, user_id="user1")
    add_feedback("TICKET-10001", "login issue", "A", False, user_id="user1")
    add_feedback("TICKET-10002", "login issue", "B", True, user_id="user1")
    add_feedback("TICKET-10000", "authentication", "B", True, user_id="user2")
    
    # Get cluster weights
    print("\nCluster Weights (based on feedback):")
    weights = get_cluster_weights()
    for cluster_type, weight in weights.items():
        print(f"  {cluster_type}: {weight:.3f}")
    
    # Get ticket boost
    print("\nTicket Boost Scores:")
    print(f"  TICKET-10000: {get_ticket_boost('TICKET-10000'):.3f}")
    print(f"  TICKET-10001: {get_ticket_boost('TICKET-10001'):.3f}")
    
    # Get statistics
    print("\nFeedback Statistics:")
    stats = get_feedback_statistics()
    print(f"  Total feedback: {stats['total_feedback']}")
    print(f"  Positive: {stats['positive_feedback']}")
    print(f"  Negative: {stats['negative_feedback']}")


def example_5_search_workflow():
    """Example: Complete search workflow (requires Neo4j)."""
    print("\n" + "=" * 70)
    print("Example 5: Search Workflow")
    print("=" * 70)
    print("\nNote: This requires Neo4j to be running with data loaded.")
    print("Run setup_cluster_benchmark.sh first.\n")
    
    try:
        from backend.search_tickets import search_tickets
        
        query = "login authentication error"
        print(f"Searching for: '{query}'")
        print("This may take a moment...\n")
        
        result = search_tickets(
            query,
            top_k=5,
            use_smart_routing=True,
            apply_feedback_boost=True
        )
        
        print(f"\nQuery: {result['query']}")
        
        if 'routing_info' in result:
            print(f"\nSmart Routing:")
            print(f"  Selected: {result['routing_info']['selected_clusters']}")
            print(f"  Explanation: {result['routing_info']['explanation']}")
        
        print("\nResults:")
        for cluster_key, cluster_result in result['results'].items():
            print(f"\n  {cluster_key.upper()}:")
            print(f"    Latency: {cluster_result['latency_ms']:.2f} ms")
            print(f"    Avg Similarity: {cluster_result['avg_similarity']:.3f}")
            print(f"    Candidates Scanned: {cluster_result['num_candidates_scanned']}")
            print(f"    Top Tickets: {len(cluster_result['top_k'])}")
            
            if cluster_result['top_k']:
                print(f"    Best Match: {cluster_result['top_k'][0]['title']}")
                print(f"      Similarity: {cluster_result['top_k'][0]['similarity']:.3f}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure:")
        print("  1. Neo4j is running (./start_docker.sh)")
        print("  2. Data is loaded (./setup_cluster_benchmark.sh)")
        print("  3. Neo4j credentials are correct")


def example_6_quality_scoring():
    """Example: Compute cluster quality metrics (requires Neo4j)."""
    print("\n" + "=" * 70)
    print("Example 6: Cluster Quality Scoring")
    print("=" * 70)
    print("\nNote: This requires Neo4j to be running with clusters loaded.\n")
    
    try:
        from backend.cluster_quality import compute_cluster_quality
        
        print("Computing quality metrics...")
        print("This may take a few minutes...\n")
        
        metrics = compute_cluster_quality()
        
        print("Quality Metrics:")
        import json
        print(json.dumps(metrics, indent=2))
        
        print("\nInterpretation:")
        print("  - quality_score: low/medium/high")
        print("  - intra_similarity: Higher = more homogeneous clusters")
        print("  - inter_distance: Higher = better separation between clusters")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure Neo4j is running and clusters are loaded.")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("CLUSTER COMPARISON SYSTEM - EXAMPLE USAGE")
    print("=" * 70)
    
    # Examples that don't require Neo4j
    example_1_generate_mock_data()
    example_2_embedding_interface()
    example_3_cluster_selection()
    example_4_relevance_feedback()
    
    # Examples that require Neo4j (will show errors if not available)
    example_5_search_workflow()
    example_6_quality_scoring()
    
    print("\n" + "=" * 70)
    print("Examples Complete!")
    print("=" * 70)
    print("\nFor full demo, run:")
    print("  1. ./start_docker.sh")
    print("  2. ./setup_cluster_benchmark.sh")
    print("  3. python3 backend/examples/example_usage.py")


if __name__ == "__main__":
    main()



