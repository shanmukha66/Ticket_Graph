"""Graph building and management with Neo4j."""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from neo4j import GraphDatabase, Driver, Session
from backend.utils.env import env


class Neo4jGraph:
    """
    Neo4j graph database operations for ticket and section management.
    
    Handles:
    - Connection management
    - Running Cypher files
    - Upserting tickets and sections
    - Batch operations
    - Similarity edge creation
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j connection."""
        self.uri = uri or env("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or env("NEO4J_USER", "neo4j")
        self.password = password or env("NEO4J_PASSWORD", "password")
        self.driver: Optional[Driver] = None
        self._cypher_dir = Path(__file__).parent / "cypher"
        
    def connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            print(f"✓ Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            raise
    
    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            print("✓ Neo4j connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def run_cypher_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Run a Cypher file containing multiple queries.
        
        Args:
            filename: Name of .cypher file in cypher/ directory
            
        Returns:
            List of results from each query
        """
        filepath = self._cypher_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Cypher file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Split by semicolons and filter out comments/empty lines
        queries = []
        for query in content.split(';'):
            query = query.strip()
            # Remove comment lines
            lines = [line for line in query.split('\n') 
                    if line.strip() and not line.strip().startswith('//')]
            query = '\n'.join(lines)
            if query:
                queries.append(query)
        
        results = []
        with self.driver.session() as session:
            for query in queries:
                try:
                    result = session.run(query)
                    results.append([dict(record) for record in result])
                except Exception as e:
                    print(f"Query failed: {query[:100]}...")
                    print(f"Error: {e}")
        
        return results
    
    def setup_constraints(self) -> None:
        """Run constraints.cypher to set up schema."""
        print("Setting up database constraints and indexes...")
        self.run_cypher_file("constraints.cypher")
        print("✓ Constraints and indexes created")
    
    def execute_query(
        self, 
        query: str, 
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a parameterized Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def upsert_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert a ticket node.
        
        Args:
            ticket_data: Dictionary with ticket properties
                Required: id
                Optional: project, priority, status, issueType, created, updated,
                         summary, description, reporter, assignee
        
        Returns:
            Created/updated ticket node data
        """
        query = """
        MERGE (t:Ticket {id: $id})
        SET t.project = $project,
            t.priority = $priority,
            t.status = $status,
            t.issueType = $issueType,
            t.created = $created,
            t.updated = $updated,
            t.summary = $summary,
            t.description = $description,
            t.reporter = $reporter,
            t.assignee = $assignee
        RETURN t
        """
        
        # Set defaults
        params = {
            'id': ticket_data.get('id'),
            'project': ticket_data.get('project', ''),
            'priority': ticket_data.get('priority', ''),
            'status': ticket_data.get('status', ''),
            'issueType': ticket_data.get('issueType', ''),
            'created': ticket_data.get('created', ''),
            'updated': ticket_data.get('updated', ''),
            'summary': ticket_data.get('summary', ''),
            'description': ticket_data.get('description', ''),
            'reporter': ticket_data.get('reporter', ''),
            'assignee': ticket_data.get('assignee', ''),
        }
        
        result = self.execute_query(query, params)
        return dict(result[0]['t']) if result else {}
    
    def upsert_section(
        self, 
        section_id: str,
        key: str,
        text: str,
        ticket_id: str
    ) -> Dict[str, Any]:
        """
        Upsert a section node and attach to ticket.
        
        Args:
            section_id: Unique section identifier
            key: Section key (e.g., 'summary', 'description', 'comment_1')
            text: Section text content
            ticket_id: Parent ticket ID
            
        Returns:
            Created/updated section node data
        """
        query = """
        MATCH (t:Ticket {id: $ticket_id})
        MERGE (s:Section {id: $id})
        SET s.key = $key,
            s.text = $text
        MERGE (t)-[:HAS_SECTION]->(s)
        RETURN s
        """
        
        params = {
            'id': section_id,
            'key': key,
            'text': text,
            'ticket_id': ticket_id
        }
        
        result = self.execute_query(query, params)
        return dict(result[0]['s']) if result else {}
    
    def batch_upsert_tickets(self, tickets: List[Dict[str, Any]]) -> int:
        """
        Batch upsert multiple tickets.
        
        Args:
            tickets: List of ticket dictionaries
            
        Returns:
            Number of tickets upserted
        """
        query = """
        UNWIND $tickets AS ticket
        MERGE (t:Ticket {id: ticket.id})
        SET t.project = ticket.project,
            t.priority = ticket.priority,
            t.status = ticket.status,
            t.issueType = ticket.issueType,
            t.created = ticket.created,
            t.updated = ticket.updated,
            t.summary = ticket.summary,
            t.description = ticket.description,
            t.reporter = ticket.reporter,
            t.assignee = ticket.assignee
        RETURN count(t) AS count
        """
        
        # Prepare tickets with defaults
        prepared_tickets = []
        for t in tickets:
            prepared_tickets.append({
                'id': t.get('id'),
                'project': t.get('project', ''),
                'priority': t.get('priority', ''),
                'status': t.get('status', ''),
                'issueType': t.get('issueType', ''),
                'created': t.get('created', ''),
                'updated': t.get('updated', ''),
                'summary': t.get('summary', ''),
                'description': t.get('description', ''),
                'reporter': t.get('reporter', ''),
                'assignee': t.get('assignee', ''),
            })
        
        result = self.execute_query(query, {'tickets': prepared_tickets})
        return result[0]['count'] if result else 0
    
    def batch_upsert_sections(self, sections: List[Dict[str, Any]]) -> int:
        """
        Batch upsert multiple sections.
        
        Args:
            sections: List of section dictionaries with keys:
                      id, key, text, ticket_id
            
        Returns:
            Number of sections upserted
        """
        query = """
        UNWIND $sections AS section
        MATCH (t:Ticket {id: section.ticket_id})
        MERGE (s:Section {id: section.id})
        SET s.key = section.key,
            s.text = section.text
        MERGE (t)-[:HAS_SECTION]->(s)
        RETURN count(s) AS count
        """
        
        result = self.execute_query(query, {'sections': sections})
        return result[0]['count'] if result else 0
    
    def create_similarity_edges(
        self,
        similarities: List[Tuple[str, str, float]],
        method: str = "cosine"
    ) -> int:
        """
        Create SIMILAR_TO relationships between tickets.
        
        Args:
            similarities: List of (from_id, to_id, score) tuples
            method: Similarity method name
            
        Returns:
            Number of edges created
        """
        query = """
        UNWIND $similarities AS sim
        MATCH (t1:Ticket {id: sim.from_id})
        MATCH (t2:Ticket {id: sim.to_id})
        MERGE (t1)-[r:SIMILAR_TO]->(t2)
        SET r.score = sim.score,
            r.method = sim.method
        RETURN count(r) AS created_count
        """
        
        sim_data = [
            {
                'from_id': from_id,
                'to_id': to_id,
                'score': float(score),
                'method': method
            }
            for from_id, to_id, score in similarities
        ]
        
        result = self.execute_query(query, {'similarities': sim_data})
        return result[0]['created_count'] if result else 0
    
    def get_ticket_with_sections(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket with all its sections."""
        query = """
        MATCH (t:Ticket {id: $ticket_id})
        OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
        RETURN t, collect(s) AS sections
        """
        
        result = self.execute_query(query, {'ticket_id': ticket_id})
        if not result:
            return None
        
        return {
            'ticket': dict(result[0]['t']),
            'sections': [dict(s) for s in result[0]['sections'] if s]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        node_query = "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count"
        rel_query = "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count"
        
        nodes = self.execute_query(node_query)
        rels = self.execute_query(rel_query)
        
        return {
            'nodes': {n['label']: n['count'] for n in nodes if n['label']},
            'relationships': {r['type']: r['count'] for r in rels}
        }


def connect_similar_tickets(
    graph: Neo4jGraph,
    ticket_embeddings: Dict[str, np.ndarray],
    threshold: float = 0.7,
    top_k: int = 10
) -> int:
    """
    Connect similar tickets using cosine similarity on embeddings.
    
    Args:
        graph: Neo4jGraph instance
        ticket_embeddings: Dict mapping ticket_id to embedding vector
        threshold: Minimum similarity score (0-1)
        top_k: Maximum number of connections per ticket
        
    Returns:
        Number of similarity edges created
    """
    ticket_ids = list(ticket_embeddings.keys())
    similarities = []
    
    print(f"Computing similarities for {len(ticket_ids)} tickets...")
    
    for i, ticket_id in enumerate(ticket_ids):
        embedding = ticket_embeddings[ticket_id]
        
        # Compute cosine similarity with all other tickets
        scores = []
        for j, other_id in enumerate(ticket_ids):
            if i == j:
                continue
            
            other_embedding = ticket_embeddings[other_id]
            
            # Cosine similarity
            score = np.dot(embedding, other_embedding) / (
                np.linalg.norm(embedding) * np.linalg.norm(other_embedding)
            )
            
            if score >= threshold:
                scores.append((other_id, float(score)))
        
        # Keep top-k similar tickets
        scores.sort(key=lambda x: x[1], reverse=True)
        for other_id, score in scores[:top_k]:
            similarities.append((ticket_id, other_id, score))
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(ticket_ids)} tickets")
    
    print(f"Creating {len(similarities)} similarity edges...")
    count = graph.create_similarity_edges(similarities, method="cosine")
    print(f"✓ Created {count} SIMILAR_TO relationships")
    
    return count

