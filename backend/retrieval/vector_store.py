"""FAISS vector store for semantic search."""
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
from backend.utils.env import env


class VectorStore:
    """
    Simple FAISS-based vector store using Inner Product (IP) for cosine similarity.
    
    Uses IndexFlatIP which computes exact inner products. Since embeddings are
    L2-normalized, inner product equals cosine similarity.
    
    Features:
    - Add texts with metadata
    - Search with k-nearest neighbors
    - Persist to disk
    - Load from disk
    """
    
    def __init__(self, index_path: str = None, dimension: int = 768):
        """
        Initialize vector store.
        
        Args:
            index_path: Path to save/load index (default from env FAISS_INDEX_PATH)
            dimension: Embedding dimension (default 768 for E5-base)
        """
        self.index_path = index_path or env(
            "FAISS_INDEX_PATH",
            "./faiss_index"
        )
        self.dimension = dimension
        
        # FAISS index (Inner Product for cosine similarity on normalized vectors)
        self.index: Optional[faiss.IndexFlatIP] = None
        
        # Metadata storage (parallel to index)
        self.metadatas: List[Dict[str, Any]] = []
        self.texts: List[str] = []
        self.vectors: List[np.ndarray] = []
        
        # Initialize empty index
        self._init_index()
    
    def _init_index(self) -> None:
        """Initialize empty FAISS index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadatas = []
        self.texts = []
        self.vectors = []
    
    def __len__(self) -> int:
        """Return number of vectors in the store."""
        return self.index.ntotal if self.index else 0
    
    def add(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add texts with their embeddings to the store.
        
        Args:
            texts: List of text strings
            embeddings: Embedding matrix (shape: [n_texts, dimension])
                       Must be L2-normalized for cosine similarity
            metadatas: Optional list of metadata dicts (one per text)
                      Should include: ticket_id, section_key, and any other fields
        """
        if len(texts) == 0:
            return
        
        # Validate embeddings
        if embeddings.shape[0] != len(texts):
            raise ValueError(
                f"Number of embeddings ({embeddings.shape[0]}) "
                f"doesn't match number of texts ({len(texts)})"
            )
        
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension ({embeddings.shape[1]}) "
                f"doesn't match index dimension ({self.dimension})"
            )
        
        # Ensure embeddings are L2-normalized
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        if not np.allclose(norms, 1.0, atol=1e-5):
            print("Warning: Embeddings not L2-normalized, normalizing now...")
            embeddings = embeddings / norms
        
        # Add to FAISS index
        embeddings_f32 = embeddings.astype(np.float32)
        self.index.add(embeddings_f32)
        
        # Store texts and metadata
        self.texts.extend(texts)
        self.vectors.extend(embeddings_f32)
        
        if metadatas is None:
            metadatas = [{}] * len(texts)
        elif len(metadatas) != len(texts):
            raise ValueError(
                f"Number of metadatas ({len(metadatas)}) "
                f"doesn't match number of texts ({len(texts)})"
            )
        
        # Ensure metadata includes text
        for i, metadata in enumerate(metadatas):
            if 'text' not in metadata:
                metadata['text'] = texts[i]
        
        self.metadatas.extend(metadatas)
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar texts.
        
        Args:
            query_embedding: Query embedding vector (L2-normalized)
            k: Number of results to return
            min_score: Minimum similarity score (0-1, optional)
            
        Returns:
            List of result dicts with keys: text, metadata, score, index
        """
        if len(self) == 0:
            return []
        
        # Ensure query is L2-normalized
        query_embedding = query_embedding.astype(np.float32)
        norm = np.linalg.norm(query_embedding)
        if not np.isclose(norm, 1.0, atol=1e-5):
            query_embedding = query_embedding / norm
        
        # Reshape for FAISS
        query_embedding = query_embedding.reshape(1, -1)
        
        # Search
        k = min(k, len(self))
        scores, indices = self.index.search(query_embedding, k)
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            # FAISS returns -1 for empty slots
            if idx == -1:
                continue
            
            # Filter by min_score if provided
            if min_score is not None and score < min_score:
                continue
            
            results.append({
                'text': self.texts[idx],
                'metadata': self.metadatas[idx].copy(),
                'score': float(score),
                'index': int(idx)
            })
        
        return results
    
    def search_batch(
        self,
        query_embeddings: np.ndarray,
        k: int = 5,
        min_score: Optional[float] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch search for multiple queries.
        
        Args:
            query_embeddings: Query embedding matrix (shape: [n_queries, dimension])
            k: Number of results per query
            min_score: Minimum similarity score
            
        Returns:
            List of result lists (one per query)
        """
        if len(self) == 0:
            return [[] for _ in range(len(query_embeddings))]
        
        # Ensure queries are L2-normalized
        query_embeddings = query_embeddings.astype(np.float32)
        norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
        query_embeddings = query_embeddings / norms
        
        # Search
        k = min(k, len(self))
        scores, indices = self.index.search(query_embeddings, k)
        
        # Build results for each query
        all_results = []
        for query_scores, query_indices in zip(scores, indices):
            results = []
            for score, idx in zip(query_scores, query_indices):
                if idx == -1:
                    continue
                if min_score is not None and score < min_score:
                    continue
                
                results.append({
                    'text': self.texts[idx],
                    'metadata': self.metadatas[idx].copy(),
                    'score': float(score),
                    'index': int(idx)
                })
            all_results.append(results)
        
        return all_results
    
    def persist(self) -> None:
        """Save index and metadata to disk."""
        # Create directory if needed
        index_dir = Path(self.index_path).parent
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = f"{self.index_path}.faiss"
        faiss.write_index(self.index, index_file)
        
        # Save metadata and texts
        meta_file = f"{self.index_path}.meta.pkl"
        with open(meta_file, 'wb') as f:
            pickle.dump({
                'metadatas': self.metadatas,
                'texts': self.texts,
                'vectors': self.vectors,
                'dimension': self.dimension
            }, f)
        
        print(f"✓ Vector store saved to {self.index_path}")
        print(f"  {len(self)} vectors, dimension={self.dimension}")
    
    def load(self) -> bool:
        """
        Load index and metadata from disk.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        index_file = f"{self.index_path}.faiss"
        meta_file = f"{self.index_path}.meta.pkl"
        
        if not os.path.exists(index_file) or not os.path.exists(meta_file):
            print(f"No existing index found at {self.index_path}")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(index_file)
            
            # Load metadata
            with open(meta_file, 'rb') as f:
                data = pickle.load(f)
                self.metadatas = data['metadatas']
                self.texts = data['texts']
                self.vectors = data['vectors']
                self.dimension = data['dimension']
            
            print(f"✓ Vector store loaded from {self.index_path}")
            print(f"  {len(self)} vectors, dimension={self.dimension}")
            return True
        
        except Exception as e:
            print(f"✗ Failed to load index: {e}")
            self._init_index()
            return False
    
    def clear(self) -> None:
        """Clear all data from the store."""
        self._init_index()
        print("✓ Vector store cleared")
    
    def get_by_ticket(self, ticket_id: str) -> List[Dict[str, Any]]:
        """
        Get all sections for a specific ticket.
        
        Args:
            ticket_id: Ticket ID to search for
            
        Returns:
            List of matching results with text and metadata
        """
        results = []
        for i, metadata in enumerate(self.metadatas):
            if metadata.get('ticket_id') == ticket_id:
                results.append({
                    'text': self.texts[i],
                    'metadata': metadata.copy(),
                    'index': i
                })
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        ticket_ids = set()
        section_keys = set()
        
        for metadata in self.metadatas:
            if 'ticket_id' in metadata:
                ticket_ids.add(metadata['ticket_id'])
            if 'section_key' in metadata:
                section_keys.add(metadata['section_key'])
        
        return {
            'total_vectors': len(self),
            'dimension': self.dimension,
            'unique_tickets': len(ticket_ids),
            'unique_section_keys': len(section_keys),
            'section_keys': sorted(section_keys),
            'index_path': self.index_path
        }

