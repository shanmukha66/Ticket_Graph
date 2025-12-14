"""
Query and Retrieval Flow for Support Tickets

This module implements cluster-aware search across all three cluster types (A, B, C).
Each cluster type uses a different strategy:
- Type A: Fast search through few large clusters
- Type B: Balanced search through medium clusters
- Type C: Precise search through many fine-grained clusters

SEARCH FLOW:
1. Embed user query using embedding model
2. For each cluster type:
   a. Find candidate clusters (compare query to cluster centroids)
   b. Retrieve tickets from candidate clusters
   c. Compute similarity scores (cosine similarity)
   d. Return top-k tickets
3. Apply feedback boosts (if enabled)
4. Return structured results with metrics

EXTENSION POINTS:
- Add new similarity metric: Modify _retrieve_and_rank_tickets
- Add custom filtering: Extend search_cluster_type
- Modify candidate selection: Change _find_candidate_clusters logic

INTEGRATIONS:
- cluster_selection.py: Smart routing for cluster selection
- relevance_feedback.py: Boost scores based on user feedback
- embedding_interface.py: Abstract embedding model interface
"""
import time
import numpy as np
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from backend.utils.env import env
from backend.cluster_selection import select_cluster_strategy
from backend.relevance_feedback import get_ticket_boost


class TicketSearcher:
    """
    Cluster-aware ticket search across all three cluster types.
    
    Search Flow:
    1. Embed user query
    2. For each cluster type (A, B, C):
       a. Find candidate clusters (compare query embedding to cluster centroids)
       b. Retrieve tickets from candidate clusters
       c. Compute similarity scores (cosine similarity)
       d. Return top-k tickets
    3. Return structured results with timing and debugging info
    """
    
    def __init__(
        self,
        neo4j_uri: str = None,
        neo4j_user: str = None,
        neo4j_password: str = None,
        embedding_model: SentenceTransformer = None
    ):
        """Initialize searcher with Neo4j connection and embedding model."""
        self.uri = neo4j_uri or env("NEO4J_URI", "bolt://localhost:7687")
        self.user = neo4j_user or env("NEO4J_USER", "neo4j")
        self.password = neo4j_password or env("NEO4J_PASSWORD", "password123")
        self.driver = None
        
        # Lazy load embedding model
        if embedding_model is None:
            print("Loading embedding model...")
            # Prefer EMBED_MODEL from env, defaulting to correct E5 identifier
            model_name = env("EMBED_MODEL", "intfloat/e5-base-v2")
            try:
                self.embedding_model = SentenceTransformer(model_name)
            except Exception:
                # Fallback to a widely available general-purpose model
                fallback_name = "sentence-transformers/all-MiniLM-L6-v2"
                print(f"  Failed to load {model_name}, falling back to {fallback_name}...")
                self.embedding_model = SentenceTransformer(fallback_name)
            print("✓ Embedding model loaded")
        else:
            self.embedding_model = embedding_model
    
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
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for user query.
        
        Args:
            query: User query string
            
        Returns:
            Normalized embedding vector (768-dimensional)
        """
        embedding = self.embedding_model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embedding
    
    def find_candidate_clusters(
        self,
        query_embedding: np.ndarray,
        cluster_type: str,
        top_clusters: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find candidate clusters by comparing query embedding to cluster centroids.
        
        Args:
            query_embedding: Query embedding vector
            cluster_type: "A", "B", or "C"
            top_clusters: Number of top clusters to return
            
        Returns:
            List of candidate clusters with similarity scores
        """
        with self.driver.session() as session:
            # Get all clusters of this type with their centroids
            query = """
            MATCH (c:Cluster {type: $cluster_type})
            WHERE c.centroid IS NOT NULL
            RETURN c.id AS cluster_id,
                   c.label AS label,
                   c.granularity_level AS granularity,
                   c.ticket_count AS ticket_count,
                   c.dominant_category AS dominant_category,
                   c.centroid AS centroid
            """
            
            result = session.run(query, cluster_type=cluster_type)
            clusters = []
            
            for record in result:
                centroid = np.array(record['centroid'])
                
                # Compute cosine similarity
                similarity = float(np.dot(query_embedding, centroid))
                
                clusters.append({
                    'cluster_id': record['cluster_id'],
                    'label': record['label'],
                    'granularity': record['granularity'],
                    'ticket_count': record['ticket_count'],
                    'dominant_category': record['dominant_category'],
                    'centroid_similarity': similarity
                })
            
            # Sort by similarity and return top clusters
            clusters.sort(key=lambda x: x['centroid_similarity'], reverse=True)
            return clusters[:top_clusters]
    
    def search_cluster_type(
        self,
        query_embedding: np.ndarray,
        cluster_type: str,
        top_k: int = 10,
        top_clusters: int = None
    ) -> Dict[str, Any]:
        """
        Search tickets using a specific cluster type.
        
        Args:
            query_embedding: Query embedding vector
            cluster_type: "A", "B", or "C"
            top_k: Number of top tickets to return
            top_clusters: Number of clusters to search (None = auto-select)
            
        Returns:
            Dictionary with results, timing, and debugging info
        """
        start_time = time.time()
        
        # Auto-select number of clusters to search based on cluster type
        if top_clusters is None:
            if cluster_type == 'A':
                top_clusters = 3  # Few clusters, search all relevant ones
            elif cluster_type == 'B':
                top_clusters = 5  # Medium number of clusters
            else:  # Type C
                top_clusters = 10  # Many clusters, search top 10
        
        # Step 1: Find candidate clusters
        cluster_selection_start = time.time()
        candidate_clusters = self.find_candidate_clusters(
            query_embedding,
            cluster_type,
            top_clusters
        )
        cluster_selection_time = time.time() - cluster_selection_start
        
        if not candidate_clusters:
            return {
                'latency_ms': (time.time() - start_time) * 1000,
                'avg_similarity': 0.0,
                'num_candidates_scanned': 0,
                'top_k': []
            }
        
        cluster_ids = [c['cluster_id'] for c in candidate_clusters]
        
        # Step 2: Retrieve tickets from candidate clusters
        ticket_retrieval_start = time.time()
        
        with self.driver.session() as session:
            query = """
            MATCH (t:Ticket)-[:BELONGS_TO {cluster_type: $cluster_type}]->(c:Cluster)
            WHERE c.id IN $cluster_ids
              AND t.embedding_vector IS NOT NULL
            RETURN t.id AS ticket_id,
                   t.title AS title,
                   t.description AS description,
                   t.category AS category,
                   t.priority AS priority,
                   t.status AS status,
                   t.created_at AS created_at,
                   t.embedding_vector AS embedding_vector,
                   c.id AS cluster_id,
                   c.label AS cluster_label
            """
            
            result = session.run(query, cluster_type=cluster_type, cluster_ids=cluster_ids)
            tickets = []
            
            for record in result:
                tickets.append({
                    'ticket_id': record['ticket_id'],
                    'title': record['title'],
                    'description': record['description'],
                    'category': record['category'],
                    'priority': record['priority'],
                    'status': record['status'],
                    'created_at': record['created_at'],
                    'embedding_vector': record['embedding_vector'],
                    'cluster_id': record['cluster_id'],
                    'cluster_label': record['cluster_label']
                })
        
        ticket_retrieval_time = time.time() - ticket_retrieval_start
        
        # Step 3: Compute similarity scores
        similarity_start = time.time()
        
        if tickets:
            embeddings = np.array([t['embedding_vector'] for t in tickets])
            similarities = np.dot(embeddings, query_embedding)
            
            # Add similarity scores to tickets
            for i, ticket in enumerate(tickets):
                ticket['similarity'] = float(similarities[i])
            
            # Sort by similarity and get top-k
            tickets.sort(key=lambda x: x['similarity'], reverse=True)
            top_tickets = tickets[:top_k]
            
            # Calculate average similarity of top-k results
            avg_similarity = float(np.mean(similarities[:top_k])) if len(similarities) >= top_k else float(np.mean(similarities))
        else:
            top_tickets = []
            similarities = np.array([])
            avg_similarity = 0.0
        
        similarity_time = time.time() - similarity_start
        total_time = time.time() - start_time
        
        # Format top_k results to match specification
        top_k_results = []
        for ticket in top_tickets:
            top_k_results.append({
                'ticket_id': ticket['ticket_id'],
                'title': ticket['title'],
                'similarity': ticket['similarity']
            })
        
        return {
            'latency_ms': total_time * 1000,
            'avg_similarity': avg_similarity,
            'num_candidates_scanned': len(tickets),
            'top_k': top_k_results
        }
    
    def search_tickets(
        self,
        query: str,
        top_k: int = 10,
        cluster_types: List[str] = None,
        use_smart_routing: bool = True,
        apply_feedback_boost: bool = True
    ) -> Dict[str, Any]:
        """
        Main search function with smart routing and feedback support.
        
        Args:
            query: User query string
            top_k: Number of top tickets to return per cluster type
            cluster_types: List of cluster types to search (None = use smart routing)
            use_smart_routing: If True, use cluster selection logic
            apply_feedback_boost: If True, apply feedback-based boosts to tickets
            
        Returns:
            Structured result with:
            - query: Original query
            - results: Results for each cluster type
            - routing_info: Cluster selection information (if smart routing used)
        """
        routing_info = None
        
        # Step 1: Smart routing (if enabled)
        if use_smart_routing and cluster_types is None:
            routing_result = select_cluster_strategy(query)
            cluster_types = [c.upper() for c in routing_result['selected_clusters']]
            routing_info = {
                'selected_clusters': cluster_types,
                'explanation': routing_result['explanation'],
                'analysis': routing_result['analysis']
            }
            print(f"\nSmart Routing: {routing_info['explanation']}")
        elif cluster_types is None:
            cluster_types = ['A', 'B', 'C']
        
        overall_start = time.time()
        
        # Step 2: Embed query
        embedding_start = time.time()
        query_embedding = self.embed_query(query)
        embedding_time = time.time() - embedding_start
        
        # Step 3: Search each cluster type
        results = {}
        
        for cluster_type in cluster_types:
            print(f"\nSearching Cluster Type {cluster_type}...")
            result = self.search_cluster_type(
                query_embedding,
                cluster_type,
                top_k=top_k
            )
            
            # Apply feedback boost if enabled
            if apply_feedback_boost:
                for ticket in result['top_k']:
                    boost = get_ticket_boost(ticket['ticket_id'])
                    original_sim = ticket['similarity']
                    ticket['similarity'] *= boost
                    ticket['original_similarity'] = original_sim  # Store original
                
                # Re-sort by boosted similarity
                result['top_k'].sort(key=lambda x: x['similarity'], reverse=True)
                result['top_k'] = result['top_k'][:top_k]  # Keep top-k
                
                # Recalculate avg_similarity
                if result['top_k']:
                    result['avg_similarity'] = sum(t['similarity'] for t in result['top_k']) / len(result['top_k'])
            
            # Map cluster type to output key format
            cluster_key = f'cluster_type_{cluster_type.lower()}'
            results[cluster_key] = result
            
            print(f"  Found {len(result['top_k'])} tickets in {result['latency_ms']:.2f} ms")
            print(f"  Scanned {result['num_candidates_scanned']} candidates")
            print(f"  Avg similarity: {result['avg_similarity']:.3f}")
            if result['top_k']:
                print(f"  Top similarity: {result['top_k'][0]['similarity']:.3f}")
        
        overall_time = time.time() - overall_start
        
        # Check if query is random/nonsensical
        def is_random_query(q: str) -> bool:
            """Detect if query appears to be random/nonsensical."""
            q_lower = q.lower().strip()
            
            # Check for patterns that suggest random text
            # 1. Repeated characters (e.g., "asdfasdf", "aaaa")
            if len(set(q_lower)) < len(q_lower) * 0.3 and len(q_lower) > 3:
                # Check if it's just repeated patterns
                if len(q_lower) > 4:
                    # Check for repeated substrings
                    for i in range(2, len(q_lower) // 2 + 1):
                        substring = q_lower[:i]
                        if q_lower.count(substring) > 1 and len(substring) * q_lower.count(substring) >= len(q_lower) * 0.8:
                            return True
            
            # 2. Very few vowels (random keyboard mashing)
            vowels = sum(1 for c in q_lower if c in 'aeiou')
            if len(q_lower) > 4 and vowels < len(q_lower) * 0.15:
                return True
            
            # 3. All same character or alternating pattern
            if len(q_lower) > 3:
                if len(set(q_lower)) <= 2:
                    return True
            
            # 4. No spaces and very long (likely random typing)
            if ' ' not in q_lower and len(q_lower) > 8:
                # Check if it looks like keyboard mashing (adjacent keys)
                adjacent_count = 0
                keyboard_rows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm']
                for i in range(len(q_lower) - 1):
                    for row in keyboard_rows:
                        if q_lower[i] in row and q_lower[i+1] in row:
                            if abs(row.index(q_lower[i]) - row.index(q_lower[i+1])) <= 2:
                                adjacent_count += 1
                                break
                if adjacent_count > len(q_lower) * 0.6:
                    return True
            
            return False
        
        # Check if results are relevant
        # Consider results irrelevant if:
        # 1. Query appears to be random/nonsensical
        # 2. Average similarity is very low (< 0.5 or 50%)
        # 3. Top result similarity is very low (< 0.55 or 55%)
        # 4. No results found
        is_relevant = True
        relevance_message = None
        
        all_results = list(results.values())
        
        # First check if query is random
        if is_random_query(query):
            is_relevant = False
            relevance_message = "Your query appears to be random text and doesn't relate to any tickets in our database. Please try searching for actual support issues, bugs, or feature requests."
        elif not all_results or all(len(r['top_k']) == 0 for r in all_results):
            is_relevant = False
            relevance_message = "No results found. Your query doesn't match any tickets in our database."
        else:
            # Check the best result across all cluster types
            best_avg_similarity = max(r['avg_similarity'] for r in all_results if r['top_k'])
            best_top_similarity = max(
                (t['similarity'] for r in all_results for t in r['top_k']),
                default=0.0
            )
            
            # Higher thresholds for relevance (50% avg, 55% top)
            if best_avg_similarity < 0.5 or best_top_similarity < 0.55:
                is_relevant = False
                relevance_message = "Your query doesn't seem to relate to any tickets in our database. Please try a different search term related to support tickets, bugs, or feature requests."
        
        output = {
            'query': query,
            'results': results,
            'is_relevant': is_relevant,
            'relevance_message': relevance_message
        }
        
        if routing_info:
            output['routing_info'] = routing_info
        
        return output


def search_tickets(
    query: str,
    top_k: int = 10,
    neo4j_uri: str = None,
    neo4j_user: str = None,
    neo4j_password: str = None,
    use_smart_routing: bool = True,
    apply_feedback_boost: bool = True,
    cluster_types: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Simple search function interface with smart routing and feedback support.
    
    Args:
        query: User query string
        top_k: Number of top tickets to return per cluster type
        neo4j_uri: Neo4j connection URI (optional)
        neo4j_user: Neo4j username (optional)
        neo4j_password: Neo4j password (optional)
        use_smart_routing: If True, automatically select cluster types based on query
        apply_feedback_boost: If True, boost tickets with positive feedback
        
    Returns:
        Structured result matching the specification:
        {
            "query": "user query text",
            "results": {
                "cluster_type_a": {
                    "latency_ms": 120,
                    "avg_similarity": 0.72,
                    "num_candidates_scanned": 850,
                    "top_k": [
                        {"ticket_id": "T123", "title": "...", "similarity": 0.81},
                        ...
                    ]
                },
                "cluster_type_b": { ... },
                "cluster_type_c": { ... }
            }
        }
        
    Example:
        >>> result = search_tickets("login issue", top_k=5)
        >>> print(result['results']['cluster_type_a']['latency_ms'])
        >>> print(result['results']['cluster_type_a']['top_k'])
    """
    searcher = TicketSearcher(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password
    )
    
    try:
        searcher.connect()
        return searcher.search_tickets(
            query,
            top_k=top_k,
            cluster_types=cluster_types,
            use_smart_routing=use_smart_routing,
            apply_feedback_boost=apply_feedback_boost,
        )
    finally:
        searcher.close()


if __name__ == "__main__":
    # Example usage
    import sys
    
    query = sys.argv[1] if len(sys.argv) > 1 else "login issue"
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    print("=" * 70)
    print("TICKET SEARCH - CLUSTER-AWARE RETRIEVAL")
    print("=" * 70)
    print(f"Query: {query}")
    print(f"Top-K: {top_k}")
    print("=" * 70)
    
    result = search_tickets(query, top_k=top_k)
    
    # Print summary
    print("\n" + "=" * 70)
    print("SEARCH RESULTS SUMMARY")
    print("=" * 70)
    print(f"Query: {result['query']}")
    
    # Print results for each cluster type
    for cluster_type in ['a', 'b', 'c']:
        cluster_key = f'cluster_type_{cluster_type}'
        if cluster_key not in result['results']:
            continue
            
        cluster_result = result['results'][cluster_key]
        print(f"\n{'='*70}")
        print(f"CLUSTER TYPE {cluster_type.upper()} RESULTS")
        print(f"{'='*70}")
        print(f"Latency: {cluster_result['latency_ms']:.2f} ms")
        print(f"Avg Similarity: {cluster_result['avg_similarity']:.3f}")
        print(f"Candidates Scanned: {cluster_result['num_candidates_scanned']}")
        print(f"Tickets Returned: {len(cluster_result['top_k'])}")
        
        if cluster_result['top_k']:
            print(f"\nTop {min(3, len(cluster_result['top_k']))} tickets:")
            for i, ticket in enumerate(cluster_result['top_k'][:3], 1):
                print(f"\n  {i}. {ticket['ticket_id']}")
                print(f"     Title: {ticket['title']}")
                print(f"     Similarity: {ticket['similarity']:.3f}")
    
    # Print JSON output
    print("\n" + "=" * 70)
    print("JSON OUTPUT")
    print("=" * 70)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))

