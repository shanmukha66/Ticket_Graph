"""
FastAPI application for Graph RAG system.

Endpoints:
- POST /ingest - Run complete ingestion pipeline
- POST /ask - Generate dual answers (general + graph RAG)
- GET /graph/subgraph - Get Cytoscape-friendly subgraph

Uses orjson for fast JSON serialization and Pydantic v2 for validation.
"""
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
import orjson

from backend.ingestors import ingest_all
from backend.llm.answer import answer_general, answer_graph_rag, retrieve_graph_context
from backend.graph.build_graph import Neo4jGraph
from backend.utils.env import env


# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================

class QueryRequest(BaseModel):
    """Request model for /ask endpoint."""
    query: str = Field(..., description="User query/question", min_length=1)
    model: str = Field(default="gpt-4", description="LLM model to use")
    top_k_sections: int = Field(default=10, ge=1, le=50, description="Number of sections for context")
    num_hops: int = Field(default=1, ge=1, le=3, description="Graph traversal hops")


class AnswerResponse(BaseModel):
    """Response model for /ask endpoint."""
    query: str
    general: Dict[str, Any]
    graph_rag: Dict[str, Any]
    provenance: Dict[str, Any]
    clusters: List[Dict[str, Any]]
    context_summary: Dict[str, Any]


class IngestRequest(BaseModel):
    """Request model for /ingest endpoint."""
    csv_path: Optional[str] = Field(default=None, description="Path to CSV file")
    jsonl_path: Optional[str] = Field(default=None, description="Path to JSONL file")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    similarity_top_k: int = Field(default=10, ge=1, le=50)
    community_algorithm: str = Field(default="louvain", pattern="^(louvain|leiden)$")


class IngestResponse(BaseModel):
    """Response model for /ingest endpoint."""
    status: str
    statistics: Dict[str, Any]
    message: str


class CytoscapeNode(BaseModel):
    """Cytoscape node format."""
    data: Dict[str, Any]


class CytoscapeEdge(BaseModel):
    """Cytoscape edge format."""
    data: Dict[str, Any]


class SubgraphResponse(BaseModel):
    """Response model for /graph/subgraph endpoint."""
    nodes: List[CytoscapeNode]
    edges: List[CytoscapeEdge]
    metadata: Dict[str, Any]


# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================

app = FastAPI(
    title="Graph RAG API",
    description="Graph-based Retrieval Augmented Generation for JIRA tickets",
    version="1.0.0",
    default_response_class=ORJSONResponse,  # Use orjson for all responses
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Graph RAG API",
        "version": "1.0.0",
        "description": "Graph-based Retrieval Augmented Generation for JIRA tickets",
        "endpoints": {
            "POST /ingest": "Run complete ingestion pipeline",
            "POST /ask": "Generate dual answers (general + graph RAG)",
            "GET /graph/subgraph": "Get Cytoscape-friendly subgraph",
            "GET /health": "Health check",
            "GET /docs": "Interactive API documentation",
            "GET /redoc": "ReDoc API documentation"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    # Check Neo4j connection
    neo4j_status = "unknown"
    try:
        with Neo4jGraph() as graph:
            stats = graph.get_stats()
            neo4j_status = "connected"
            neo4j_nodes = sum(stats.get('nodes', {}).values())
    except Exception as e:
        neo4j_status = f"error: {str(e)}"
        neo4j_nodes = 0
    
    # Check vector store
    vector_store_status = "unknown"
    try:
        from backend.retrieval.vector_store import VectorStore
        vs = VectorStore()
        if vs.load():
            vector_store_status = "loaded"
            vector_count = len(vs)
        else:
            vector_store_status = "not_found"
            vector_count = 0
    except Exception as e:
        vector_store_status = f"error: {str(e)}"
        vector_count = 0
    
    return {
        "status": "healthy",
        "services": {
            "neo4j": {
                "status": neo4j_status,
                "nodes": neo4j_nodes
            },
            "vector_store": {
                "status": vector_store_status,
                "vectors": vector_count
            }
        }
    }


@app.post("/ingest", response_model=IngestResponse)
async def ingest_data(request: IngestRequest):
    """
    Run complete ingestion pipeline.
    
    Steps:
    1. Setup Neo4j constraints
    2. Load CSV data (if path provided)
    3. Load JSONL data (if path provided)
    4. Build similarity edges
    5. Run community detection
    
    Returns statistics about ingestion.
    """
    try:
        print("\n" + "="*70)
        print("STARTING INGESTION VIA API")
        print("="*70)
        
        # Run ingestion
        stats = ingest_all(
            csv_path=request.csv_path,
            jsonl_path=request.jsonl_path,
            similarity_threshold=request.similarity_threshold,
            similarity_top_k=request.similarity_top_k,
            community_algorithm=request.community_algorithm
        )
        
        return IngestResponse(
            status="success",
            statistics=stats,
            message=f"Ingestion complete: {stats['total_tickets']} tickets, "
                   f"{stats['total_sections']} sections, "
                   f"{stats['similarity_edges']} edges, "
                   f"{stats['communities']} communities"
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QueryRequest):
    """
    Generate dual answers for a query.
    
    Returns both:
    - General answer (no context)
    - Graph RAG answer (with context, citations, provenance)
    
    Also includes:
    - Provenance (tickets, sections, communities)
    - Clusters involved
    - Context summary
    """
    try:
        print(f"\n[API] Query: {request.query}")
        
        # Generate general answer
        print("[API] Generating general answer...")
        general_result = answer_general(
            query=request.query,
            model=request.model
        )
        
        # Generate graph RAG answer
        print("[API] Generating graph RAG answer...")
        graph_rag_result = answer_graph_rag(
            query=request.query,
            top_k_sections=request.top_k_sections,
            num_hops=request.num_hops,
            model=request.model
        )
        
        # Check for errors
        if 'error' in general_result or 'error' in graph_rag_result:
            error_msg = general_result.get('error') or graph_rag_result.get('error')
            raise HTTPException(
                status_code=500,
                detail=f"Answer generation failed: {error_msg}"
            )
        
        # Build response
        return AnswerResponse(
            query=request.query,
            general=general_result,
            graph_rag=graph_rag_result,
            provenance=graph_rag_result.get('provenance', {}),
            clusters=graph_rag_result.get('clusters', []),
            context_summary=graph_rag_result.get('context_summary', {})
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        )


@app.get("/graph/subgraph", response_model=SubgraphResponse)
async def get_subgraph(
    query: str = Query(..., description="Search query to find relevant subgraph"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of sections to retrieve"),
    num_hops: int = Query(default=1, ge=1, le=3, description="Graph traversal hops"),
    include_communities: bool = Query(default=True, description="Include community info")
):
    """
    Get Cytoscape-friendly subgraph for visualization.
    
    Returns nodes and edges in Cytoscape.js format:
    - Nodes: {data: {id, label, type, communityId, score, ...}}
    - Edges: {data: {id, source, target, rel, score, ...}}
    
    Process:
    1. Vector search to find relevant sections
    2. Extract ticket IDs
    3. Query Neo4j for subgraph
    4. Format for Cytoscape
    """
    try:
        print(f"\n[API] Subgraph query: {query}")
        
        # Retrieve graph context
        context = retrieve_graph_context(
            query=query,
            top_k_sections=top_k,
            num_hops=num_hops
        )
        
        if 'error' in context:
            raise HTTPException(
                status_code=404,
                detail=context['error']
            )
        
        # Build Cytoscape format
        cytoscape_nodes = []
        cytoscape_edges = []
        
        # Get ticket IDs from context
        ticket_ids = context['provenance']['ticket_ids']
        
        # Query Neo4j for full subgraph
        with Neo4jGraph() as graph:
            # Get tickets with sections and similarities
            query_cypher = """
            MATCH (t:Ticket)
            WHERE t.id IN $ticket_ids
            
            OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
            
            OPTIONAL MATCH (t)-[sim:SIMILAR_TO]-(other:Ticket)
            WHERE other.id IN $ticket_ids
            
            RETURN t, 
                   collect(DISTINCT s) AS sections,
                   collect(DISTINCT {
                       other: other,
                       score: sim.score,
                       id: id(sim)
                   }) AS similarities
            """
            
            results = graph.execute_query(query_cypher, {'ticket_ids': ticket_ids})
            
            # Process results
            ticket_nodes = {}
            section_nodes = {}
            edges = []
            
            for record in results:
                ticket = record['t']
                ticket_id = ticket['id']
                
                # Add ticket node with full information
                ticket_nodes[ticket_id] = {
                    'data': {
                        'id': ticket_id,
                        'label': ticket.get('summary', ticket_id)[:50],
                        'type': 'Ticket',
                        'communityId': ticket.get('communityId'),
                        'project': ticket.get('project', ''),
                        'status': ticket.get('status', ''),
                        'priority': ticket.get('priority', ''),
                        'summary': ticket.get('summary', ''),  # Full summary
                        'text': ticket.get('text_for_rag', ''),  # Full ticket description/text
                        'created': ticket.get('created', ''),
                        'updated': ticket.get('updated', ''),
                        'score': 1.0  # Base score, will be updated from vector search
                    }
                }
                
                # Add section nodes
                for section in record['sections']:
                    if section:
                        section_id = section['id']
                        section_nodes[section_id] = {
                            'data': {
                                'id': section_id,
                                'label': section['key'],
                                'type': 'Section',
                                'key': section['key'],
                                'text': section.get('text', '')[:100]
                            }
                        }
                        
                        # Add HAS_SECTION edge
                        edges.append({
                            'data': {
                                'id': f"{ticket_id}-has-{section_id}",
                                'source': ticket_id,
                                'target': section_id,
                                'rel': 'HAS_SECTION'
                            }
                        })
                
                # Add similarity edges
                for sim in record['similarities']:
                    if sim['other'] and sim['score']:
                        other_id = sim['other']['id']
                        # Avoid duplicate edges (undirected)
                        edge_id = f"{min(ticket_id, other_id)}-sim-{max(ticket_id, other_id)}"
                        
                        edges.append({
                            'data': {
                                'id': edge_id,
                                'source': ticket_id,
                                'target': other_id,
                                'rel': 'SIMILAR_TO',
                                'score': float(sim['score'])
                            }
                        })
            
            # Update ticket scores from vector search results
            for section in context['sections']:
                ticket_id = section['metadata'].get('ticket_id')
                if ticket_id and ticket_id in ticket_nodes:
                    # Use max score across sections
                    current_score = ticket_nodes[ticket_id]['data'].get('score', 0)
                    ticket_nodes[ticket_id]['data']['score'] = max(
                        current_score,
                        section['score']
                    )
            
            # Convert to lists
            cytoscape_nodes = list(ticket_nodes.values())
            
            # Optionally include section nodes
            if len(section_nodes) < 50:  # Limit for performance
                cytoscape_nodes.extend(list(section_nodes.values()))
            
            # Remove duplicate edges
            unique_edges = {}
            for edge in edges:
                edge_id = edge['data']['id']
                if edge_id not in unique_edges:
                    unique_edges[edge_id] = edge
            cytoscape_edges = list(unique_edges.values())
            
            # Build metadata
            metadata = {
                'query': query,
                'num_tickets': len(ticket_nodes),
                'num_sections': len(section_nodes),
                'num_edges': len(cytoscape_edges),
                'communities': []
            }
            
            # Add community info if requested
            if include_communities:
                communities_in_graph = set()
                for node in ticket_nodes.values():
                    comm_id = node['data'].get('communityId')
                    if comm_id is not None:
                        communities_in_graph.add(comm_id)
                
                for comm in context.get('community_context', []):
                    if comm['community_id'] in communities_in_graph:
                        metadata['communities'].append({
                            'id': comm['community_id'],
                            'size': comm['size'],
                            'reason': comm['reason']
                        })
        
        return SubgraphResponse(
            nodes=[CytoscapeNode(**node) for node in cytoscape_nodes],
            edges=[CytoscapeEdge(**edge) for edge in cytoscape_edges],
            metadata=metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve subgraph: {str(e)}"
        )


# ==============================================================================
# RUN APPLICATION
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = env("APP_HOST", "127.0.0.1")
    port = int(env("APP_PORT", "8000"))
    
    print(f"\n{'='*70}")
    print("STARTING GRAPH RAG API")
    print(f"{'='*70}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Docs: http://{host}:{port}/docs")
    print(f"{'='*70}\n")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True
    )

