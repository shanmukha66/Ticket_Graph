"""Search API endpoints."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import SearchQuery, SearchResponse, SearchResult
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search(query: SearchQuery):
    """Perform semantic search using FAISS."""
    try:
        # Generate query embedding
        query_embedding = embedding_service.encode(query.query)
        
        # Search in FAISS
        results = faiss_service.search(
            query_embedding,
            top_k=query.top_k,
            threshold=query.threshold,
        )
        
        # Format results
        search_results = []
        for idx, score in results:
            doc, metadata = faiss_service.get_document(idx)
            search_results.append(
                SearchResult(
                    id=str(idx),
                    text=doc,
                    score=score,
                    metadata=metadata,
                )
            )
        
        return SearchResponse(results=search_results, query=query.query)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
async def index_documents(documents: list[str], metadata: list[dict] = None):
    """Index documents for search."""
    try:
        # Generate embeddings
        embeddings = embedding_service.encode_batch(documents)
        
        # Add to FAISS index
        faiss_service.add_vectors(embeddings, documents, metadata)
        
        # Save index
        faiss_service.save_index()
        
        return {
            "message": f"Indexed {len(documents)} documents",
            "total_documents": len(faiss_service.documents),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def clear_index():
    """Clear the search index."""
    try:
        faiss_service.clear()
        return {"message": "Search index cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

