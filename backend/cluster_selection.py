"""
Cluster Selection Logic (Smart Routing)

Implements heuristics to decide which cluster type(s) to use based on query characteristics.
"""
from typing import List, Dict, Any, Tuple
import re


class ClusterSelector:
    """
    Smart routing to select optimal cluster type(s) based on query analysis.
    
    Decision factors:
    - Query length (short queries → coarse clusters, long queries → fine clusters)
    - Keyword presence (specific technical terms → fine clusters)
    - Query complexity (simple → coarse, complex → fine)
    """
    
    # Keywords that suggest need for precise/fine-grained search
    PRECISION_KEYWORDS = [
        'specific', 'exact', 'precise', 'detailed', 'exact error',
        'specific issue', 'particular', 'exact problem'
    ]
    
    # Keywords that suggest broad/coarse search is sufficient
    BROAD_KEYWORDS = [
        'overview', 'general', 'all', 'list', 'show me',
        'what', 'how many', 'summary', 'overall'
    ]
    
    # Technical/complex keywords that suggest fine-grained clusters
    TECHNICAL_KEYWORDS = [
        'error', 'exception', 'bug', 'crash', 'failure',
        'timeout', 'deadlock', 'memory leak', 'performance',
        'authentication', 'authorization', 'database', 'api'
    ]
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to determine characteristics.
        
        Returns:
            Dictionary with query analysis metrics
        """
        query_lower = query.lower().strip()
        query_length = len(query.split())
        
        # Count keyword matches
        precision_count = sum(1 for kw in self.PRECISION_KEYWORDS if kw in query_lower)
        broad_count = sum(1 for kw in self.BROAD_KEYWORDS if kw in query_lower)
        technical_count = sum(1 for kw in self.TECHNICAL_KEYWORDS if kw in query_lower)
        
        # Estimate complexity
        has_question_mark = '?' in query
        has_multiple_terms = query_length > 5
        has_technical_terms = technical_count > 0
        
        complexity_score = (
            (1 if has_question_mark else 0) +
            (1 if has_multiple_terms else 0) +
            (1 if has_technical_terms else 0)
        )
        
        return {
            'query_length': query_length,
            'precision_keywords': precision_count,
            'broad_keywords': broad_count,
            'technical_keywords': technical_count,
            'complexity_score': complexity_score,
            'has_question': has_question_mark,
            'is_technical': has_technical_terms
        }
    
    def select_clusters(self, query: str) -> Tuple[List[str], str]:
        """
        Select which cluster type(s) to use based on query analysis.
        
        Returns:
            Tuple of (list of cluster types to use, explanation string)
        """
        analysis = self.analyze_query(query)
        
        query_length = analysis['query_length']
        precision_keywords = analysis['precision_keywords']
        broad_keywords = analysis['broad_keywords']
        technical_keywords = analysis['technical_keywords']
        complexity_score = analysis['complexity_score']
        
        # Decision logic
        
        # Very short queries (< 3 words) → use coarse clusters (fast)
        if query_length <= 2:
            return ['A'], f"Short query ({query_length} words) - using Cluster Type A (coarse) for fast results"
        
        # Explicit precision keywords → use fine-grained clusters
        if precision_keywords > 0:
            return ['C'], f"Precision keywords detected - using Cluster Type C (fine-grained) for accurate results"
        
        # Explicit broad keywords → use coarse clusters
        if broad_keywords > 0:
            return ['A'], f"Broad keywords detected - using Cluster Type A (coarse) for general results"
        
        # Technical queries with high complexity → use fine-grained clusters
        if technical_keywords >= 2 and complexity_score >= 2:
            return ['C'], f"Complex technical query ({technical_keywords} technical terms) - using Cluster Type C (fine-grained)"
        
        # Technical queries → use balanced clusters
        if technical_keywords > 0:
            return ['B'], f"Technical query detected ({technical_keywords} technical terms) - using Cluster Type B (balanced)"
        
        # Medium length queries → use balanced clusters
        if 3 <= query_length <= 6:
            return ['B'], f"Medium-length query ({query_length} words) - using Cluster Type B (balanced)"
        
        # Long queries (> 6 words) → use fine-grained clusters
        if query_length > 6:
            return ['C'], f"Long query ({query_length} words) - using Cluster Type C (fine-grained) for detailed results"
        
        # Default: use all three for comparison
        return ['A', 'B', 'C'], f"Standard query - using all cluster types (A, B, C) for comparison"
    
    def select_clusters_with_fallback(self, query: str, always_include_all: bool = False) -> Tuple[List[str], str]:
        """
        Select clusters with option to always include all types for comparison.
        
        Args:
            query: User query
            always_include_all: If True, always return all three types
            
        Returns:
            Tuple of (list of cluster types, explanation)
        """
        if always_include_all:
            return ['A', 'B', 'C'], "Using all cluster types for comprehensive comparison"
        
        return self.select_clusters(query)


def select_cluster_strategy(query: str, always_include_all: bool = False) -> Dict[str, Any]:
    """
    Simple interface for cluster selection.
    
    Args:
        query: User query string
        always_include_all: If True, always use all cluster types
        
    Returns:
        Dictionary with:
        - selected_clusters: List of cluster types to use
        - explanation: Why these clusters were selected
        - analysis: Query analysis details
    """
    selector = ClusterSelector()
    analysis = selector.analyze_query(query)
    selected_clusters, explanation = selector.select_clusters_with_fallback(query, always_include_all)
    
    return {
        'selected_clusters': selected_clusters,
        'explanation': explanation,
        'analysis': analysis
    }

