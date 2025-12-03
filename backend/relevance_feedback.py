"""
Relevance Feedback System

Simple interface to accept user feedback on search results and show how it could be
used to adjust cluster weights and scoring in the future.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path


class RelevanceFeedbackStore:
    """
    Store user feedback on search results.
    
    Feedback can be used to:
    - Adjust cluster weights (prefer clusters with positive feedback)
    - Adjust similarity scoring (boost tickets with positive feedback)
    - Improve cluster selection logic
    """
    
    def __init__(self, storage_path: str = "./mnt/data/feedback.json"):
        """
        Initialize feedback store.
        
        Args:
            storage_path: Path to store feedback data (JSON file)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self.feedback_data = {
            'ticket_feedback': {},  # ticket_id -> list of feedback entries
            'cluster_feedback': defaultdict(list),  # cluster_type -> list of feedback
            'query_feedback': defaultdict(list),  # query -> list of feedback
            'statistics': {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0
            }
        }
        
        # Load existing feedback if available
        self.load()
    
    def load(self):
        """Load feedback from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.feedback_data = json.load(f)
                print(f"Loaded {self.feedback_data['statistics']['total_feedback']} feedback entries")
            except Exception as e:
                print(f"Warning: Could not load feedback: {e}")
    
    def save(self):
        """Save feedback to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save feedback: {e}")
    
    def add_feedback(
        self,
        ticket_id: str,
        query: str,
        cluster_type: str,
        is_relevant: bool,
        user_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add user feedback for a ticket result.
        
        Args:
            ticket_id: Ticket ID that was shown
            query: Original query
            cluster_type: Cluster type used ("A", "B", or "C")
            is_relevant: True if ticket was relevant, False otherwise
            user_id: Optional user identifier
            notes: Optional notes/explanation
            
        Returns:
            Feedback entry dictionary
        """
        feedback_entry = {
            'ticket_id': ticket_id,
            'query': query,
            'cluster_type': cluster_type,
            'is_relevant': is_relevant,
            'user_id': user_id,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store feedback
        if ticket_id not in self.feedback_data['ticket_feedback']:
            self.feedback_data['ticket_feedback'][ticket_id] = []
        
        self.feedback_data['ticket_feedback'][ticket_id].append(feedback_entry)
        self.feedback_data['cluster_feedback'][cluster_type].append(feedback_entry)
        self.feedback_data['query_feedback'][query].append(feedback_entry)
        
        # Update statistics
        self.feedback_data['statistics']['total_feedback'] += 1
        if is_relevant:
            self.feedback_data['statistics']['positive_feedback'] += 1
        else:
            self.feedback_data['statistics']['negative_feedback'] += 1
        
        # Save to disk
        self.save()
        
        return feedback_entry
    
    def get_ticket_feedback(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a specific ticket."""
        return self.feedback_data['ticket_feedback'].get(ticket_id, [])
    
    def get_cluster_feedback(self, cluster_type: str) -> List[Dict[str, Any]]:
        """Get all feedback for a specific cluster type."""
        return self.feedback_data['cluster_feedback'].get(cluster_type, [])
    
    def compute_cluster_weights(self) -> Dict[str, float]:
        """
        Compute cluster weights based on feedback.
        
        Clusters with more positive feedback get higher weights.
        
        Returns:
            Dictionary mapping cluster_type -> weight (0.0-1.0)
        """
        weights = {'A': 0.33, 'B': 0.33, 'C': 0.33}  # Default equal weights
        
        total_feedback = self.feedback_data['statistics']['total_feedback']
        if total_feedback == 0:
            return weights
        
        # Compute positive feedback ratio for each cluster type
        for cluster_type in ['A', 'B', 'C']:
            feedback_list = self.feedback_data['cluster_feedback'].get(cluster_type, [])
            if not feedback_list:
                continue
            
            positive_count = sum(1 for f in feedback_list if f['is_relevant'])
            total_count = len(feedback_list)
            
            if total_count > 0:
                positive_ratio = positive_count / total_count
                # Weight based on positive ratio (normalized)
                weights[cluster_type] = positive_ratio
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def compute_ticket_boost(self, ticket_id: str) -> float:
        """
        Compute boost score for a ticket based on feedback.
        
        Tickets with positive feedback get a boost, negative feedback gets a penalty.
        
        Returns:
            Boost multiplier (e.g., 1.2 for positive feedback, 0.8 for negative)
        """
        feedback_list = self.get_ticket_feedback(ticket_id)
        
        if not feedback_list:
            return 1.0  # No boost
        
        positive_count = sum(1 for f in feedback_list if f['is_relevant'])
        negative_count = len(feedback_list) - positive_count
        
        # Simple boost calculation
        # More positive feedback = higher boost
        # More negative feedback = lower boost
        boost = 1.0 + (positive_count * 0.1) - (negative_count * 0.1)
        
        # Clamp between 0.5 and 2.0
        return max(0.5, min(2.0, boost))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        stats = self.feedback_data['statistics'].copy()
        
        # Add per-cluster statistics
        stats['per_cluster'] = {}
        for cluster_type in ['A', 'B', 'C']:
            feedback_list = self.get_cluster_feedback(cluster_type)
            stats['per_cluster'][cluster_type] = {
                'total': len(feedback_list),
                'positive': sum(1 for f in feedback_list if f['is_relevant']),
                'negative': sum(1 for f in feedback_list if not f['is_relevant'])
            }
        
        return stats


# Global feedback store instance
_feedback_store: Optional[RelevanceFeedbackStore] = None


def get_feedback_store() -> RelevanceFeedbackStore:
    """Get or create global feedback store instance."""
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = RelevanceFeedbackStore()
    return _feedback_store


def add_feedback(
    ticket_id: str,
    query: str,
    cluster_type: str,
    is_relevant: bool,
    user_id: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simple interface to add feedback.
    
    Args:
        ticket_id: Ticket ID
        query: Original query
        cluster_type: "A", "B", or "C"
        is_relevant: True if relevant, False otherwise
        user_id: Optional user ID
        notes: Optional notes
        
    Returns:
        Feedback entry
    """
    store = get_feedback_store()
    return store.add_feedback(ticket_id, query, cluster_type, is_relevant, user_id, notes)


def get_cluster_weights() -> Dict[str, float]:
    """
    Get cluster weights based on feedback.
    
    Returns:
        Dictionary mapping cluster_type -> weight
    """
    store = get_feedback_store()
    return store.compute_cluster_weights()


def get_ticket_boost(ticket_id: str) -> float:
    """
    Get boost score for a ticket based on feedback.
    
    Returns:
        Boost multiplier
    """
    store = get_feedback_store()
    return store.compute_ticket_boost(ticket_id)


def get_feedback_statistics() -> Dict[str, Any]:
    """Get feedback statistics."""
    store = get_feedback_store()
    return store.get_statistics()

