"""Community detection using Neo4j GDS algorithms."""
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
import re
from backend.graph.build_graph import Neo4jGraph


class CommunityDetector:
    """
    Community detection and analysis using Neo4j Graph Data Science.
    
    Supports:
    - Louvain community detection
    - Leiden community detection (if available)
    - Community statistics and analysis
    - Representative ticket selection
    """
    
    def __init__(self, graph: Neo4jGraph):
        """Initialize with Neo4j graph connection."""
        self.graph = graph
    
    def _ensure_projection(self, graph_name: str = 'ticket-similarity-graph') -> bool:
        """Ensure graph projection exists, create if not."""
        try:
            # Check if projection exists
            check_query = """
            CALL gds.graph.exists($graph_name)
            YIELD exists
            RETURN exists
            """
            result = self.graph.execute_query(check_query, {'graph_name': graph_name})
            
            if result and result[0]['exists']:
                return True
            
            # Create projection
            print(f"Creating graph projection: {graph_name}")
            create_query = """
            CALL gds.graph.project(
                $graph_name,
                'Ticket',
                {
                    SIMILAR_TO: {
                        orientation: 'UNDIRECTED',
                        properties: 'score'
                    }
                }
            )
            YIELD graphName, nodeCount, relationshipCount
            RETURN graphName, nodeCount, relationshipCount
            """
            result = self.graph.execute_query(create_query, {'graph_name': graph_name})
            
            if result:
                print(f"✓ Projection created: {result[0]['nodeCount']} nodes, "
                      f"{result[0]['relationshipCount']} relationships")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error ensuring projection: {e}")
            return False
    
    def drop_projection(self, graph_name: str = 'ticket-similarity-graph') -> None:
        """Drop a graph projection."""
        try:
            query = "CALL gds.graph.drop($graph_name) YIELD graphName"
            self.graph.execute_query(query, {'graph_name': graph_name})
            print(f"✓ Dropped projection: {graph_name}")
        except Exception as e:
            print(f"Note: Could not drop projection (may not exist): {e}")
    
    def run_louvain(
        self,
        graph_name: str = 'ticket-similarity-graph',
        write: bool = True
    ) -> Dict[str, Any]:
        """
        Run Louvain community detection.
        
        Args:
            graph_name: Name of graph projection
            write: If True, write communityId to nodes
            
        Returns:
            Dictionary with community detection results
        """
        # Ensure projection exists
        if not self._ensure_projection(graph_name):
            raise RuntimeError("Failed to create graph projection")
        
        try:
            if write:
                # Run and write to graph
                query = """
                CALL gds.louvain.write($graph_name, {
                    writeProperty: 'communityId',
                    relationshipWeightProperty: 'score',
                    includeIntermediateCommunities: false
                })
                YIELD communityCount, modularity, modularities
                RETURN communityCount, modularity, modularities
                """
                
                result = self.graph.execute_query(query, {'graph_name': graph_name})
                
                if result:
                    info = result[0]
                    print(f"✓ Louvain: {info['communityCount']} communities, "
                          f"modularity={info['modularity']:.4f}")
                    return info
            else:
                # Stream results without writing
                query = """
                CALL gds.louvain.stream($graph_name, {
                    relationshipWeightProperty: 'score'
                })
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).id AS ticketId, communityId
                """
                
                results = self.graph.execute_query(query, {'graph_name': graph_name})
                return {
                    'communities': {r['ticketId']: r['communityId'] for r in results},
                    'communityCount': len(set(r['communityId'] for r in results))
                }
        
        except Exception as e:
            print(f"Error running Louvain: {e}")
            raise
    
    def run_leiden(
        self,
        graph_name: str = 'ticket-similarity-graph',
        write: bool = True,
        gamma: float = 1.0,
        theta: float = 0.01
    ) -> Dict[str, Any]:
        """
        Run Leiden community detection (if available in GDS).
        
        Args:
            graph_name: Name of graph projection
            write: If True, write communityId to nodes
            gamma: Resolution parameter
            theta: Tolerance parameter
            
        Returns:
            Dictionary with community detection results
        """
        if not self._ensure_projection(graph_name):
            raise RuntimeError("Failed to create graph projection")
        
        try:
            if write:
                query = """
                CALL gds.leiden.write($graph_name, {
                    writeProperty: 'communityId',
                    relationshipWeightProperty: 'score',
                    gamma: $gamma,
                    theta: $theta
                })
                YIELD communityCount, modularity
                RETURN communityCount, modularity
                """
                
                params = {
                    'graph_name': graph_name,
                    'gamma': gamma,
                    'theta': theta
                }
                
                result = self.graph.execute_query(query, params)
                
                if result:
                    info = result[0]
                    print(f"✓ Leiden: {info['communityCount']} communities, "
                          f"modularity={info.get('modularity', 'N/A')}")
                    return info
            else:
                query = """
                CALL gds.leiden.stream($graph_name, {
                    relationshipWeightProperty: 'score',
                    gamma: $gamma,
                    theta: $theta
                })
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).id AS ticketId, communityId
                """
                
                params = {
                    'graph_name': graph_name,
                    'gamma': gamma,
                    'theta': theta
                }
                
                results = self.graph.execute_query(query, params)
                return {
                    'communities': {r['ticketId']: r['communityId'] for r in results},
                    'communityCount': len(set(r['communityId'] for r in results))
                }
        
        except Exception as e:
            print(f"Leiden not available or error: {e}")
            print("Falling back to Louvain...")
            return self.run_louvain(graph_name, write)
    
    def get_community_stats(self) -> Dict[str, Any]:
        """Get statistics about communities."""
        query = """
        MATCH (t:Ticket)
        WHERE t.communityId IS NOT NULL
        RETURN t.communityId AS communityId, count(t) AS size
        ORDER BY size DESC
        """
        
        results = self.graph.execute_query(query)
        
        community_sizes = {r['communityId']: r['size'] for r in results}
        
        return {
            'num_communities': len(community_sizes),
            'sizes': community_sizes,
            'total_nodes': sum(community_sizes.values()),
            'avg_size': sum(community_sizes.values()) / len(community_sizes) if community_sizes else 0,
            'largest_size': max(community_sizes.values()) if community_sizes else 0,
            'smallest_size': min(community_sizes.values()) if community_sizes else 0
        }
    
    def get_community_members(self, community_id: int) -> List[Dict[str, Any]]:
        """Get all tickets in a community with their sections."""
        query = """
        MATCH (t:Ticket {communityId: $community_id})
        OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
        RETURN t, collect(s) AS sections
        ORDER BY t.id
        """
        
        results = self.graph.execute_query(query, {'community_id': community_id})
        
        return [
            {
                'ticket': dict(r['t']),
                'sections': [dict(s) for s in r['sections'] if s]
            }
            for r in results
        ]
    
    def get_top_tickets_per_community(
        self, 
        top_n: int = 5
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get top N representative tickets from each community.
        
        Selection is based on degree centrality (number of connections).
        
        Args:
            top_n: Number of top tickets per community
            
        Returns:
            Dict mapping community_id to list of top tickets
        """
        # Calculate degree for each ticket
        query = """
        MATCH (t:Ticket)
        WHERE t.communityId IS NOT NULL
        OPTIONAL MATCH (t)-[r:SIMILAR_TO]-()
        WITH t, count(r) AS degree
        ORDER BY t.communityId, degree DESC
        WITH t.communityId AS communityId, 
             collect({ticket: t, degree: degree})[0..$top_n] AS topTickets
        RETURN communityId, topTickets
        """
        
        results = self.graph.execute_query(query, {'top_n': top_n})
        
        top_tickets = {}
        for r in results:
            community_id = r['communityId']
            tickets = [
                {
                    'id': item['ticket']['id'],
                    'summary': item['ticket'].get('summary', ''),
                    'project': item['ticket'].get('project', ''),
                    'degree': item['degree']
                }
                for item in r['topTickets']
            ]
            top_tickets[community_id] = tickets
        
        return top_tickets
    
    def analyze_community_text(self, community_id: int, top_terms: int = 10) -> List[str]:
        """
        Analyze text in a community to find frequent terms.
        
        Args:
            community_id: Community to analyze
            top_terms: Number of top terms to return
            
        Returns:
            List of most frequent meaningful terms
        """
        # Get all section text for community
        query = """
        MATCH (t:Ticket {communityId: $community_id})-[:HAS_SECTION]->(s:Section)
        RETURN collect(s.text) AS texts
        """
        
        results = self.graph.execute_query(query, {'community_id': community_id})
        
        if not results or not results[0]['texts']:
            return []
        
        # Combine all text
        all_text = ' '.join(results[0]['texts']).lower()
        
        # Extract words (simple tokenization)
        words = re.findall(r'\b[a-z]{3,}\b', all_text)
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'was', 'this', 'that', 'with', 'have', 'from', 'they', 'will',
            'been', 'has', 'had', 'were', 'said', 'their', 'what', 'than',
            'when', 'where', 'who', 'which', 'these', 'those', 'then', 'into'
        }
        
        words = [w for w in words if w not in stop_words]
        
        # Count frequencies
        word_counts = Counter(words)
        
        # Return top terms
        return [word for word, count in word_counts.most_common(top_terms)]
    
    def generate_community_summary(
        self,
        community_id: int,
        top_tickets: int = 3,
        top_terms: int = 8
    ) -> Dict[str, Any]:
        """
        Generate a summary for a community.
        
        Args:
            community_id: Community to summarize
            top_tickets: Number of representative tickets
            top_terms: Number of frequent terms
            
        Returns:
            Dictionary with community summary
        """
        # Get members
        members = self.get_community_members(community_id)
        
        # Get top tickets (by degree)
        query = """
        MATCH (t:Ticket {communityId: $community_id})
        OPTIONAL MATCH (t)-[r:SIMILAR_TO]-()
        WITH t, count(r) AS degree
        ORDER BY degree DESC
        LIMIT $top_n
        RETURN t.id AS id, 
               t.summary AS summary, 
               t.project AS project,
               degree
        """
        
        top_ticket_results = self.graph.execute_query(
            query,
            {'community_id': community_id, 'top_n': top_tickets}
        )
        
        # Get frequent terms
        frequent_terms = self.analyze_community_text(community_id, top_terms)
        
        # Generate reason/description
        reason = f"Common themes: {', '.join(frequent_terms[:5])}" if frequent_terms else "Similar tickets"
        
        return {
            'community_id': community_id,
            'size': len(members),
            'top_tickets': top_ticket_results,
            'frequent_terms': frequent_terms,
            'reason': reason
        }
    
    def get_full_analysis(
        self,
        algorithm: str = 'louvain',
        top_tickets_per_community: int = 3
    ) -> Dict[str, Any]:
        """
        Run community detection and generate full analysis.
        
        Args:
            algorithm: 'louvain' or 'leiden'
            top_tickets_per_community: Number of representative tickets
            
        Returns:
            Complete community analysis with clusters, sizes, representatives, and reasons
        """
        print(f"\nRunning {algorithm.upper()} community detection...")
        
        # Run algorithm
        if algorithm.lower() == 'leiden':
            self.run_leiden(write=True)
        else:
            self.run_louvain(write=True)
        
        # Get statistics
        stats = self.get_community_stats()
        print(f"✓ Found {stats['num_communities']} communities")
        print(f"  Avg size: {stats['avg_size']:.1f}, "
              f"Largest: {stats['largest_size']}, "
              f"Smallest: {stats['smallest_size']}")
        
        # Analyze each community
        print("\nAnalyzing communities...")
        community_summaries = []
        
        for community_id in sorted(stats['sizes'].keys()):
            summary = self.generate_community_summary(
                community_id,
                top_tickets=top_tickets_per_community
            )
            community_summaries.append(summary)
            print(f"  Community {community_id}: {summary['size']} tickets - {summary['reason']}")
        
        return {
            'algorithm': algorithm,
            'num_communities': stats['num_communities'],
            'cluster_sizes': stats['sizes'],
            'statistics': stats,
            'communities': community_summaries
        }

