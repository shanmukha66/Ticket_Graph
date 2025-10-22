"""Embeddings API endpoints."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import EmbeddingRequest, EmbeddingResponse
from app.services.embedding_service import embedding_service

router = APIRouter()


@router.post("/", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """Generate embedding for a text."""
    try:
        embedding = embedding_service.encode(request.text)
        return EmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_embedding_info():
    """Get information about the embedding model."""
    return {
        "model": embedding_service.model_name,
        "dimension": embedding_service.get_dimension(),
        "loaded": embedding_service.is_loaded(),
    }

