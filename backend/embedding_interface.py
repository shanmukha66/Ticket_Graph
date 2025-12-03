"""
Embedding interface abstraction for ticket embeddings.

Supports both real models (sentence-transformers) and mock vectors for testing.
"""
from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of embedding vectors."""
        pass
    
    @abstractmethod
    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text.
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            numpy array of embeddings (shape: (1, dim) or (n, dim))
        """
        pass


class SentenceTransformerEmbedding(EmbeddingModel):
    """Real embedding model using sentence-transformers."""
    
    def __init__(self, model_name: str = "intfloat/e5-base-v2"):
        """
        Initialize sentence transformer model.
        
        Args:
            model_name: HuggingFace model name
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
        print(f"✓ Model loaded. Dimension: {self._dimension}")
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension
    
    def embed(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings.
        
        Args:
            text: Single text or list of texts
            normalize: Whether to normalize embeddings (default: True)
            
        Returns:
            numpy array of embeddings
        """
        embeddings = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Ensure 2D array
        if isinstance(text, str):
            embeddings = embeddings.reshape(1, -1)
        
        return embeddings


class MockEmbedding(EmbeddingModel):
    """Mock embedding model for testing (generates random vectors)."""
    
    def __init__(self, dimension: int = 768, seed: int = 42):
        """
        Initialize mock embedding model.
        
        Args:
            dimension: Embedding dimension (default: 768)
            seed: Random seed for reproducibility
        """
        self._dimension = dimension
        self.rng = np.random.RandomState(seed)
        print(f"✓ Mock embedding model initialized. Dimension: {dimension}")
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension
    
    def embed(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Generate random embeddings.
        
        Args:
            text: Single text or list of texts (ignored, generates random)
            normalize: Whether to normalize embeddings (default: True)
            
        Returns:
            numpy array of random embeddings
        """
        if isinstance(text, str):
            embeddings = self.rng.randn(1, self._dimension)
        else:
            embeddings = self.rng.randn(len(text), self._dimension)
        
        if normalize:
            # L2 normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-8)
        
        return embeddings


def get_embedding_model(use_mock: bool = False, model_name: str = None) -> EmbeddingModel:
    """
    Factory function to get embedding model.
    
    Args:
        use_mock: If True, return mock model (default: False)
        model_name: Model name for real model (default: e5-base-v2)
        
    Returns:
        EmbeddingModel instance
    """
    if use_mock:
        return MockEmbedding(dimension=768)
    else:
        model_name = model_name or "intfloat/e5-base-v2"
        return SentenceTransformerEmbedding(model_name=model_name)


# Example usage
if __name__ == "__main__":
    # Test real model
    print("Testing real embedding model...")
    model = get_embedding_model(use_mock=False)
    text = "Cannot login with email"
    embedding = model.embed(text)
    print(f"Text: '{text}'")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding sample: {embedding[0, :5]}")
    
    # Test mock model
    print("\nTesting mock embedding model...")
    mock_model = get_embedding_model(use_mock=True)
    embedding = mock_model.embed(text)
    print(f"Text: '{text}'")
    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding sample: {embedding[0, :5]}")

