"""Graph API endpoints."""
from typing import Optional
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    NodeCreate,
    RelationshipCreate,
    Node,
    Relationship,
    GraphResponse,
    CommunityDetectionRequest,
    CommunityDetectionResponse,
)
from app.services.neo4j_service import neo4j_service

router = APIRouter()


@router.post("/nodes", response_model=Node)
async def create_node(node: NodeCreate):
    """Create a new node in the graph."""
    try:
        result = neo4j_service.create_node(node.label, node.properties)
        return Node(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relationships", response_model=Relationship)
async def create_relationship(relationship: RelationshipCreate):
    """Create a new relationship between nodes."""
    try:
        result = neo4j_service.create_relationship(
            relationship.from_node_id,
            relationship.to_node_id,
            relationship.relationship_type,
            relationship.properties,
        )
        return Relationship(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=GraphResponse)
async def get_graph(limit: int = 100):
    """Get all nodes and relationships from the graph."""
    try:
        nodes = neo4j_service.get_all_nodes(limit)
        relationships = neo4j_service.get_all_relationships(limit)
        return GraphResponse(
            nodes=[Node(**n) for n in nodes],
            relationships=[Relationship(**r) for r in relationships],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/communities", response_model=CommunityDetectionResponse)
async def detect_communities(request: CommunityDetectionRequest):
    """Run community detection on the graph."""
    try:
        if request.algorithm.lower() == "louvain":
            communities = neo4j_service.run_louvain(request.weight_property)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported algorithm: {request.algorithm}",
            )
        
        return CommunityDetectionResponse(
            communities=communities,
            num_communities=len(set(communities.values())),
            algorithm=request.algorithm,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def clear_graph():
    """Clear all nodes and relationships from the graph."""
    try:
        neo4j_service.clear_database()
        return {"message": "Graph cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

