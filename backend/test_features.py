"""
Test script for the three additional features:
1. Cluster selection logic (smart routing)
2. Cluster quality scoring
3. Relevance feedback
"""
from backend.cluster_selection import select_cluster_strategy
from backend.cluster_quality import compute_cluster_quality
from backend.relevance_feedback import add_feedback, get_cluster_weights, get_feedback_statistics


def test_cluster_selection():
    """Test cluster selection logic."""
    print("=" * 70)
    print("TESTING CLUSTER SELECTION LOGIC")
    print("=" * 70)
    
    test_queries = [
        "login",  # Short query
        "specific authentication error with OAuth token",  # Precision keywords
        "show me all tickets",  # Broad keywords
        "database connection timeout performance issue",  # Technical, complex
        "payment error",  # Technical, simple
        "how to fix bug",  # Medium length
        "detailed explanation of the exact problem with API endpoint returning 500 error"  # Long query
    ]
    
    for query in test_queries:
        result = select_cluster_strategy(query)
        print(f"\nQuery: '{query}'")
        print(f"  Selected: {result['selected_clusters']}")
        print(f"  Explanation: {result['explanation']}")
        print(f"  Analysis: {result['analysis']}")


def test_cluster_quality():
    """Test cluster quality scoring."""
    print("\n" + "=" * 70)
    print("TESTING CLUSTER QUALITY SCORING")
    print("=" * 70)
    print("\nNote: This requires Neo4j to be running with clusters loaded.")
    print("Computing quality metrics...\n")
    
    try:
        results = compute_cluster_quality()
        print("\nQuality Metrics:")
        import json
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Neo4j is running and clusters are loaded.")


def test_relevance_feedback():
    """Test relevance feedback system."""
    print("\n" + "=" * 70)
    print("TESTING RELEVANCE FEEDBACK")
    print("=" * 70)
    
    # Add some sample feedback
    print("\nAdding sample feedback...")
    
    add_feedback("TICKET-10000", "login issue", "A", True, user_id="user1")
    add_feedback("TICKET-10001", "login issue", "A", False, user_id="user1")
    add_feedback("TICKET-10002", "login issue", "B", True, user_id="user1")
    add_feedback("TICKET-10000", "authentication error", "B", True, user_id="user2")
    add_feedback("TICKET-10003", "payment error", "C", True, user_id="user1")
    
    print("✓ Feedback added")
    
    # Get cluster weights
    print("\nCluster Weights (based on feedback):")
    weights = get_cluster_weights()
    for cluster_type, weight in weights.items():
        print(f"  {cluster_type}: {weight:.3f}")
    
    # Get ticket boost
    print("\nTicket Boost Scores:")
    print(f"  TICKET-10000: {get_ticket_boost('TICKET-10000'):.3f}")
    print(f"  TICKET-10001: {get_ticket_boost('TICKET-10001'):.3f}")
    print(f"  TICKET-10002: {get_ticket_boost('TICKET-10002'):.3f}")
    
    # Get statistics
    print("\nFeedback Statistics:")
    stats = get_feedback_statistics()
    import json
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    test_cluster_selection()
    test_cluster_quality()
    test_relevance_feedback()

