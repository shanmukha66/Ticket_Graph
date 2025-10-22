"""Answer generation using LLM with general and graph RAG approaches."""
from typing import Dict, List, Any, Optional, Tuple
import os
from collections import defaultdict
from openai import OpenAI

from backend.utils.env import env
from backend.retrieval.embedder import Embedder
from backend.retrieval.vector_store import VectorStore
from backend.graph.build_graph import Neo4jGraph
from backend.graph.community import CommunityDetector
from backend.llm.prompts import (
    GENERAL_PROMPT,
    build_graph_rag_prompt
)

# Initialize OpenAI client
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client."""
    global _openai_client
    if _openai_client is None:
        api_key = env('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


# ==============================================================================
# GENERAL ANSWER - Using OpenAI without context
# ==============================================================================

def answer_general(query: str, model: str = "gpt-4") -> Dict[str, Any]:
    """
    Generate a general help-desk style answer using OpenAI.
    
    Args:
        query: User question
        model: OpenAI model to use
        
    Returns:
        Dictionary with answer and metadata
    """
    # Get API key
    api_key = env("OPENAI_API_KEY")
    if not api_key or api_key == "sk-...":
        return {
            "answer": "Error: OPENAI_API_KEY not configured in .env file",
            "error": "missing_api_key",
            "model": None
        }
    
    # Build prompt
    prompt = GENERAL_PROMPT.format(query=query)
    
    try:
        # Call OpenAI using new v1.0+ API
        client = get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful technical support assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "model": model,
            "tokens": response.usage.total_tokens,
            "approach": "general"
        }
    
    except Exception as e:
        return {
            "answer": f"Error calling OpenAI API: {str(e)}",
            "error": str(e),
            "model": model
        }


# ==============================================================================
# GRAPH CONTEXT RETRIEVAL
# ==============================================================================

def retrieve_graph_context(
    query: str,
    top_k_sections: int = 10,
    num_hops: int = 1,
    similarity_threshold: float = 0.7,
    max_similar_tickets: int = 5
) -> Dict[str, Any]:
    """
    Retrieve comprehensive graph context for a query.
    
    Steps:
    1. Vector search to find top N relevant sections
    2. Extract ticket IDs from sections
    3. Expand to N-hop subgraph via Neo4j
    4. Get community/cluster information
    5. Rank and organize snippets
    
    Args:
        query: User query
        top_k_sections: Number of sections to retrieve from vector search
        num_hops: Number of hops for graph expansion
        similarity_threshold: Minimum similarity for graph edges
        max_similar_tickets: Max similar tickets to include per seed ticket
        
    Returns:
        Dictionary with sections, graph_context, community_context, and provenance
    """
    # Initialize services
    embedder = Embedder()
    embedder.load()
    
    vector_store = VectorStore()
    if not vector_store.load():
        return {
            "sections": [],
            "graph_context": {},
            "community_context": [],
            "provenance": {},
            "error": "Vector store not found. Run ingestion first."
        }
    
    # Step 1: Vector search
    print(f"Searching for: {query}")
    query_embedding = embedder.embed_query(query)
    sections = vector_store.search(query_embedding, k=top_k_sections)
    
    if not sections:
        return {
            "sections": [],
            "graph_context": {},
            "community_context": [],
            "provenance": {},
            "error": "No relevant sections found"
        }
    
    print(f"Found {len(sections)} relevant sections")
    
    # Step 2: Extract ticket IDs
    ticket_ids = list(set(
        s['metadata']['ticket_id'] 
        for s in sections 
        if 'ticket_id' in s['metadata']
    ))
    
    print(f"Extracted {len(ticket_ids)} unique tickets")
    
    # Step 3: Expand to subgraph via Neo4j
    graph_context = {}
    with Neo4jGraph() as graph:
        # Get subgraph with similar tickets
        query_cypher = """
        MATCH (t:Ticket)
        WHERE t.id IN $ticket_ids
        
        // Get sections
        OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
        
        // Get similar tickets (without nesting collect)
        OPTIONAL MATCH (t)-[sim:SIMILAR_TO]->(similar:Ticket)
        WHERE sim.score >= $threshold
        
        WITH t, 
             collect(DISTINCT {id: s.id, key: s.key, text: s.text}) AS sections,
             collect(DISTINCT {
                 id: similar.id,
                 summary: similar.summary,
                 score: sim.score,
                 communityId: similar.communityId
             }) AS similar_tickets
        
        RETURN t.id AS ticket_id,
               t.summary AS summary,
               t.communityId AS communityId,
               sections,
               similar_tickets[0..$max_similar] AS similar_tickets
        """
        
        results = graph.execute_query(query_cypher, {
            'ticket_ids': ticket_ids,
            'threshold': similarity_threshold,
            'max_similar': max_similar_tickets
        })
        
        # Process results
        all_tickets = []
        all_similar = []
        communities = set()
        
        for record in results:
            ticket_id = record['ticket_id']
            community_id = record.get('communityId')
            
            if community_id is not None:
                communities.add(community_id)
            
            all_tickets.append({
                'id': ticket_id,
                'summary': record.get('summary', ''),
                'communityId': community_id,
                'sections': record['sections']
            })
            
            # Add similar tickets
            for sim in record.get('similar_tickets', []):
                if sim and sim.get('id'):
                    all_similar.append(sim)
                    if sim.get('communityId') is not None:
                        communities.add(sim['communityId'])
        
        # Calculate statistics
        num_nodes = len(all_tickets) + len(set(s['id'] for s in all_similar))
        num_relationships = sum(len(r.get('similar_tickets', [])) for r in results)
        
        # Get top tickets by degree (number of connections)
        ticket_degrees = defaultdict(int)
        for record in results:
            ticket_id = record['ticket_id']
            ticket_degrees[ticket_id] = len(record.get('similar_tickets', []))
        
        top_tickets = sorted(
            all_tickets,
            key=lambda t: ticket_degrees.get(t['id'], 0),
            reverse=True
        )[:5]
        
        graph_context = {
            'num_similar': len(all_similar),
            'num_hops': num_hops,
            'num_nodes': num_nodes,
            'num_relationships': num_relationships,
            'top_tickets': [
                {
                    'id': t['id'],
                    'summary': t['summary'],
                    'degree': ticket_degrees.get(t['id'], 0)
                }
                for t in top_tickets
            ],
            'seed_tickets': ticket_ids,
            'all_tickets': all_tickets,
            'similar_tickets': all_similar
        }
        
        # Step 4: Get community information
        community_context = []
        if communities:
            detector = CommunityDetector(graph)
            
            for community_id in sorted(communities):
                try:
                    summary = detector.generate_community_summary(
                        community_id,
                        top_tickets=3,
                        top_terms=8
                    )
                    community_context.append(summary)
                except Exception as e:
                    print(f"Warning: Could not get community {community_id} summary: {e}")
        
        print(f"Retrieved graph context: {num_nodes} nodes, "
              f"{num_relationships} relationships, "
              f"{len(community_context)} communities")
    
    # Build provenance
    provenance = {
        'ticket_ids': ticket_ids,
        'section_ids': [s['metadata'].get('section_id') for s in sections],
        'community_ids': list(communities),
        'num_sections': len(sections),
        'num_tickets': len(ticket_ids),
        'num_communities': len(communities)
    }
    
    return {
        'sections': sections,
        'graph_context': graph_context,
        'community_context': community_context,
        'provenance': provenance
    }


# ==============================================================================
# GRAPH RAG ANSWER - Using OpenAI with graph context
# ==============================================================================

def answer_graph_rag(
    query: str,
    top_k_sections: int = 10,
    num_hops: int = 1,
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Generate a graph RAG answer with citations and provenance.
    
    Args:
        query: User query
        top_k_sections: Number of sections for vector search
        num_hops: Graph expansion hops
        model: OpenAI model to use
        
    Returns:
        Dictionary with:
        - answer: LLM-generated answer
        - provenance: Ticket IDs, sections, communities used
        - context: Retrieved context for transparency
        - clusters: Clusters involved with reasons
        - top_nodes: Most relevant tickets
        - edges: Relationships used
        - reasoning: Short reasons per cluster
    """
    try:
        import openai
    except ImportError:
        raise ImportError(
            "OpenAI library not installed. "
            "Install with: pip install openai"
        )
    
    # Get API key
    api_key = env("OPENAI_API_KEY")
    if not api_key or api_key == "sk-...":
        return {
            "answer": "Error: OPENAI_API_KEY not configured in .env file",
            "error": "missing_api_key",
            "provenance": {}
        }
    
    openai.api_key = api_key
    
    # Retrieve graph context
    print(f"\nRetrieving graph context for: {query}")
    context = retrieve_graph_context(
        query,
        top_k_sections=top_k_sections,
        num_hops=num_hops
    )
    
    if 'error' in context:
        return {
            "answer": f"Error retrieving context: {context['error']}",
            "error": context['error'],
            "provenance": {}
        }
    
    # Build prompt
    prompt = build_graph_rag_prompt(
        query,
        context['sections'],
        context['graph_context'],
        context['community_context']
    )
    
    # Call OpenAI using new v1.0+ API
    print("Generating answer with LLM...")
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical support assistant with access to a knowledge graph of past issues."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        answer = response.choices[0].message.content
        
        # Build comprehensive response
        return {
            "answer": answer,
            "provenance": context['provenance'],
            "model": model,
            "tokens": response.usage.total_tokens,
            "approach": "graph_rag",
            
            # Graph analysis details
            "clusters": [
                {
                    "cluster_id": c['community_id'],
                    "size": c['size'],
                    "reason": c['reason'],
                    "top_tickets": [t['id'] for t in c.get('top_tickets', [])]
                }
                for c in context['community_context']
            ],
            
            "top_nodes": context['graph_context'].get('top_tickets', []),
            
            "edges": {
                "total": context['graph_context'].get('num_relationships', 0),
                "threshold": 0.7,
                "description": f"{context['graph_context'].get('num_relationships', 0)} similarity connections used"
            },
            
            "reasoning": {
                f"cluster_{c['community_id']}": c['reason']
                for c in context['community_context']
            },
            
            # Context for transparency
            "context_summary": {
                "sections_retrieved": len(context['sections']),
                "tickets_involved": len(context['provenance']['ticket_ids']),
                "communities_analyzed": len(context['community_context']),
                "graph_nodes": context['graph_context'].get('num_nodes', 0),
                "graph_edges": context['graph_context'].get('num_relationships', 0)
            }
        }
    
    except Exception as e:
        return {
            "answer": f"Error calling OpenAI API: {str(e)}",
            "error": str(e),
            "provenance": context['provenance'],
            "model": model
        }


# ==============================================================================
# DUAL ANSWER - Compare both approaches
# ==============================================================================

def answer_dual(query: str, model: str = "gpt-4") -> Dict[str, Any]:
    """
    Generate both general and graph RAG answers for comparison.
    
    Args:
        query: User query
        model: OpenAI model to use
        
    Returns:
        Dictionary with both answers and comparison metadata
    """
    print("\n" + "="*70)
    print("GENERATING DUAL ANSWERS")
    print("="*70)
    
    # General answer
    print("\n[1/2] Generating general answer...")
    general = answer_general(query, model=model)
    
    # Graph RAG answer
    print("\n[2/2] Generating graph RAG answer...")
    graph_rag = answer_graph_rag(query, model=model)
    
    print("\n" + "="*70)
    print("DUAL ANSWERS COMPLETE")
    print("="*70)
    
    return {
        "query": query,
        "general": general,
        "graph_rag": graph_rag,
        "comparison": {
            "general_length": len(general.get('answer', '')),
            "graph_rag_length": len(graph_rag.get('answer', '')),
            "citations_count": len(graph_rag.get('provenance', {}).get('ticket_ids', [])),
            "communities_used": len(graph_rag.get('provenance', {}).get('community_ids', []))
        }
    }

