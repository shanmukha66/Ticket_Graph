"""Pydantic schemas for request/response models."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NodeCreate(BaseModel):
    """Schema for creating a node."""
    label: str = Field(..., description="Node label/type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")


class RelationshipCreate(BaseModel):
    """Schema for creating a relationship."""
    from_node_id: str = Field(..., description="Source node ID")
    to_node_id: str = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")


class Node(BaseModel):
    """Schema for a graph node."""
    id: str
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    """Schema for a graph relationship."""
    id: str
    type: str
    from_node: str
    to_node: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphResponse(BaseModel):
    """Schema for graph data response."""
    nodes: List[Node]
    relationships: List[Relationship]


class SearchQuery(BaseModel):
    """Schema for search query."""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity threshold")


class SearchResult(BaseModel):
    """Schema for a search result."""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Schema for search response."""
    results: List[SearchResult]
    query: str


class EmbeddingRequest(BaseModel):
    """Schema for embedding request."""
    text: str = Field(..., description="Text to embed")


class EmbeddingResponse(BaseModel):
    """Schema for embedding response."""
    embedding: List[float]
    dimension: int


class CommunityDetectionRequest(BaseModel):
    """Schema for community detection request."""
    algorithm: str = Field(default="louvain", description="Algorithm to use: louvain or leiden")
    weight_property: Optional[str] = Field(default=None, description="Edge weight property")


class CommunityDetectionResponse(BaseModel):
    """Schema for community detection response."""
    communities: Dict[str, int]
    num_communities: int
    algorithm: str

