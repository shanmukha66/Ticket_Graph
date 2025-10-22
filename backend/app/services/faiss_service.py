"""FAISS vector search service."""
import os
from typing import List, Tuple, Optional
import numpy as np
import faiss
from pathlib import Path
from app.core.config import settings


class FAISSService:
    """Service for FAISS vector search operations."""
    
    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.index_path = settings.FAISS_INDEX_PATH
        self.dimension: Optional[int] = None
        self.documents: List[str] = []
        self.metadata: List[dict] = []
    
    def initialize(self, dimension: int = 768):
        """Initialize FAISS index."""
        try:
            self.dimension = dimension
            
            # Try to load existing index
            if os.path.exists(f"{self.index_path}.index"):
                self.load_index()
                print(f"Loaded existing FAISS index from {self.index_path}")
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
                print(f"Created new FAISS index with dimension {dimension}")
        except Exception as e:
            print(f"Failed to initialize FAISS: {e}")
            self.index = None
    
    def is_initialized(self) -> bool:
        """Check if FAISS index is initialized."""
        return self.index is not None
    
    def add_vectors(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadata: List[dict] = None
    ):
        """Add vectors to the index."""
        if not self.index:
            raise RuntimeError("FAISS index not initialized")
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store documents and metadata
        self.documents.extend(texts)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(texts))
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Tuple[int, float]]:
        """Search for similar vectors."""
        if not self.index:
            raise RuntimeError("FAISS index not initialized")
        
        # Normalize query vector
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Filter by threshold if provided
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            if threshold is None or score >= threshold:
                results.append((int(idx), float(score)))
        
        return results
    
    def get_document(self, idx: int) -> Tuple[str, dict]:
        """Get document and metadata by index."""
        if idx < 0 or idx >= len(self.documents):
            raise IndexError(f"Document index {idx} out of range")
        return self.documents[idx], self.metadata[idx]
    
    def save_index(self):
        """Save FAISS index to disk."""
        if not self.index:
            raise RuntimeError("FAISS index not initialized")
        
        # Create directory if it doesn't exist
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save index
        faiss.write_index(self.index, f"{self.index_path}.index")
        
        # Save documents and metadata
        import pickle
        with open(f"{self.index_path}.meta", "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata,
                "dimension": self.dimension
            }, f)
        
        print(f"FAISS index saved to {self.index_path}")
    
    def load_index(self):
        """Load FAISS index from disk."""
        # Load index
        self.index = faiss.read_index(f"{self.index_path}.index")
        
        # Load documents and metadata
        import pickle
        with open(f"{self.index_path}.meta", "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.metadata = data["metadata"]
            self.dimension = data["dimension"]
        
        print(f"FAISS index loaded from {self.index_path}")
    
    def clear(self):
        """Clear the index."""
        if self.dimension:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            self.metadata = []


# Global instance
faiss_service = FAISSService()

