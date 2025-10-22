"""Text embedding service using sentence-transformers E5 model."""
from typing import List, Union
import numpy as np
import torch
import os
from sentence_transformers import SentenceTransformer
from backend.utils.env import env


class Embedder:
    """
    Text embedding service using sentence-transformers E5 model.
    
    E5 (Text Embeddings by Weakly-Supervised Contrastive Pre-training)
    is a state-of-the-art embedding model that works well for semantic search.
    
    The model produces 768-dimensional embeddings that are L2-normalized
    for efficient cosine similarity computation using inner product.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedder with E5 model.
        
        Args:
            model_name: HuggingFace model name (default from env EMBED_MODEL)
        """
        self.model_name = model_name or env(
            "EMBED_MODEL",
            "sentence-transformers/e5-base-v2"
        )
        self.model = None
        self._dimension = None
    
    def load(self, num_threads: int = 15) -> None:
        """
        Load the embedding model with multi-core support.
        
        Args:
            num_threads: Number of CPU threads to use (default: 15)
        """
        if self.model is not None:
            print(f"Model already loaded: {self.model_name}")
            return
        
        # Set PyTorch to use multiple threads for CPU operations
        torch.set_num_threads(num_threads)
        os.environ['OMP_NUM_THREADS'] = str(num_threads)
        os.environ['MKL_NUM_THREADS'] = str(num_threads)
        
        print(f"Loading embedding model: {self.model_name}")
        print(f"(Using {num_threads} CPU threads for acceleration)")
        print("(First time may take a few minutes to download ~500MB)")
        
        try:
            self.model = SentenceTransformer(self.model_name)
            self._dimension = self.model.get_sentence_embedding_dimension()
            print(f"✓ Model loaded: {self.model_name}")
            print(f"  Embedding dimension: {self._dimension}")
            print(f"  CPU threads: {torch.get_num_threads()}")
        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            raise
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            if self.model is not None:
                self._dimension = self.model.get_sentence_embedding_dimension()
            else:
                # Default for E5-base-v2
                self._dimension = 768
        return self._dimension
    
    def _prepare_text(self, text: str, is_query: bool = False) -> str:
        """
        Prepare text for E5 model.
        
        E5 models benefit from instruction prefixes:
        - "query: " for search queries
        - "passage: " for documents to be searched
        
        Args:
            text: Input text
            is_query: True if this is a search query, False for documents
            
        Returns:
            Text with appropriate prefix
        """
        text = text.strip()
        
        # Add E5 prefix if using E5 model
        if "e5" in self.model_name.lower():
            prefix = "query: " if is_query else "passage: "
            if not text.startswith(prefix):
                text = prefix + text
        
        return text
    
    def embed_text(
        self,
        text: str,
        normalize: bool = True,
        is_query: bool = False
    ) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            normalize: If True, L2-normalize the embedding
            is_query: True if this is a search query
            
        Returns:
            L2-normalized embedding vector (numpy array)
        """
        if self.model is None:
            self.load()
        
        # Prepare text
        prepared_text = self._prepare_text(text, is_query=is_query)
        
        # Generate embedding
        embedding = self.model.encode(
            prepared_text,
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )
        
        return embedding.astype(np.float32)
    
    def embed_texts(
        self,
        texts: List[str],
        normalize: bool = True,
        is_query: bool = False,
        batch_size: int = 32,
        show_progress: bool = False,
        num_workers: int = 8  # Use 8 parallel workers for data loading
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts with multi-core support.
        
        Args:
            texts: List of input texts
            normalize: If True, L2-normalize embeddings
            is_query: True if these are search queries
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            num_workers: Number of parallel workers (default: 8)
            
        Returns:
            L2-normalized embedding matrix (shape: [n_texts, dimension])
        """
        if self.model is None:
            self.load()
        
        if not texts:
            return np.array([]).reshape(0, self.dimension)
        
        # Prepare texts in parallel
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            prepared_texts = list(executor.map(
                lambda t: self._prepare_text(t, is_query=is_query),
                texts
            ))
        
        # Generate embeddings with multi-processing
        embeddings = self.model.encode(
            prepared_texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            device='cpu',  # Force CPU to use all threads
            num_workers=num_workers  # Parallel data loading
        )
        
        return embeddings.astype(np.float32)
    
    def embed_query(self, query: str, normalize: bool = True) -> np.ndarray:
        """
        Convenience method for embedding a search query.
        
        Args:
            query: Search query text
            normalize: If True, L2-normalize the embedding
            
        Returns:
            L2-normalized query embedding
        """
        return self.embed_text(query, normalize=normalize, is_query=True)
    
    def embed_documents(
        self,
        documents: List[str],
        normalize: bool = True,
        batch_size: int = 32,
        show_progress: bool = False,
        num_workers: int = 8
    ) -> np.ndarray:
        """
        Convenience method for embedding documents with multi-core support.
        
        Args:
            documents: List of document texts
            normalize: If True, L2-normalize embeddings
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            num_workers: Number of parallel workers (default: 8)
            
        Returns:
            L2-normalized embedding matrix
        """
        return self.embed_texts(
            documents,
            normalize=normalize,
            is_query=False,
            batch_size=batch_size,
            show_progress=show_progress,
            num_workers=num_workers
        )


# Global embedder instance
_global_embedder = None


def get_embedder() -> Embedder:
    """Get or create global embedder instance."""
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = Embedder()
        _global_embedder.load()
    return _global_embedder

