"""
Ticket Search API endpoint for cluster-aware search.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from backend.search_tickets import search_tickets

# Prefix '/search' so the full path is POST /search/tickets
router = APIRouter(prefix="/search", tags=["search"])


class TicketSearchRequest(BaseModel):
    """Request model for ticket search."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of top tickets to return")
    use_smart_routing: bool = Field(default=True, description="Use smart cluster selection")
    apply_feedback_boost: bool = Field(default=True, description="Apply feedback-based boosts")
    cluster_types: Optional[List[str]] = Field(
        default=None,
        description="Optional list of cluster types to search (e.g., ['A', 'B', 'C']). "
                    "If provided, smart routing can be disabled to use manual selection."
    )


@router.post("/tickets")
async def search_tickets_endpoint(request: TicketSearchRequest) -> Dict[str, Any]:
    """
    Search tickets using cluster-aware retrieval.
    
    Returns results from all three cluster types (A, B, C) with:
    - Top-k tickets per cluster type
    - Latency metrics
    - Average similarity scores
    - Number of candidates scanned
    - Routing information (if smart routing enabled)
    """
    try:
        result = search_tickets(
            query=request.query,
            top_k=request.top_k,
            cluster_types=request.cluster_types,
            use_smart_routing=request.use_smart_routing,
            apply_feedback_boost=request.apply_feedback_boost
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

