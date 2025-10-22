"""Embedding service using sentence-transformers."""
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings


class EmbeddingService:
    """Service for generating embeddings using E5 model."""
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.model_name = settings.EMBEDDING_MODEL
    
    def load_model(self):
        """Load the embedding model."""
        try:
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            print(f"Model loaded successfully. Embedding dimension: {self.get_dimension()}")
        except Exception as e:
            print(f"Failed to load embedding model: {e}")
            self.model = None
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if not self.model:
            return 0
        return self.model.get_sentence_embedding_dimension()
    
    def encode(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        # E5 models benefit from instruction prefixes
        if "e5" in self.model_name.lower():
            text = f"query: {text}"
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        # Add E5 prefix if needed
        if "e5" in self.model_name.lower():
            texts = [f"passage: {text}" for text in texts]
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings


# Global instance
embedding_service = EmbeddingService()

