"""Neo4j database service."""
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from app.core.config import settings


class Neo4jService:
    """Service for Neo4j database operations."""
    
    def __init__(self):
        self.driver: Optional[Driver] = None
    
    def connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            print(f"Connected to Neo4j at {settings.NEO4J_URI}")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")
    
    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        return self.driver is not None
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a node in Neo4j."""
        with self.driver.session() as session:
            result = session.run(
                f"CREATE (n:{label} $properties) RETURN n, id(n) as node_id",
                properties=properties
            )
            record = result.single()
            node = record["n"]
            return {
                "id": str(record["node_id"]),
                "label": label,
                "properties": dict(node)
            }
    
    def create_relationship(
        self,
        from_node_id: str,
        to_node_id: str,
        rel_type: str,
        properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two nodes."""
        properties = properties or {}
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (a), (b)
                WHERE id(a) = $from_id AND id(b) = $to_id
                CREATE (a)-[r:{rel_type} $properties]->(b)
                RETURN r, id(r) as rel_id, id(a) as from_id, id(b) as to_id
                """,
                from_id=int(from_node_id),
                to_id=int(to_node_id),
                properties=properties
            )
            record = result.single()
            if not record:
                raise ValueError("Failed to create relationship")
            
            rel = record["r"]
            return {
                "id": str(record["rel_id"]),
                "type": rel_type,
                "from_node": str(record["from_id"]),
                "to_node": str(record["to_id"]),
                "properties": dict(rel)
            }
    
    def get_all_nodes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all nodes from the database."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n) RETURN n, id(n) as node_id, labels(n) as labels LIMIT $limit",
                limit=limit
            )
            nodes = []
            for record in result:
                node = record["n"]
                nodes.append({
                    "id": str(record["node_id"]),
                    "label": record["labels"][0] if record["labels"] else "Node",
                    "properties": dict(node)
                })
            return nodes
    
    def get_all_relationships(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all relationships from the database."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a)-[r]->(b)
                RETURN r, id(r) as rel_id, type(r) as rel_type,
                       id(a) as from_id, id(b) as to_id
                LIMIT $limit
                """,
                limit=limit
            )
            relationships = []
            for record in result:
                rel = record["r"]
                relationships.append({
                    "id": str(record["rel_id"]),
                    "type": record["rel_type"],
                    "from_node": str(record["from_id"]),
                    "to_node": str(record["to_id"]),
                    "properties": dict(rel)
                })
            return relationships
    
    def run_louvain(self, weight_property: Optional[str] = None) -> Dict[str, int]:
        """Run Louvain community detection algorithm."""
        with self.driver.session() as session:
            # Create graph projection
            session.run("""
                CALL gds.graph.project(
                    'tempGraph',
                    '*',
                    '*'
                )
            """)
            
            # Run Louvain
            query = """
                CALL gds.louvain.stream('tempGraph')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).id as nodeKey, communityId
            """
            result = session.run(query)
            communities = {record["nodeKey"]: record["communityId"] for record in result}
            
            # Drop projection
            session.run("CALL gds.graph.drop('tempGraph')")
            
            return communities
    
    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")


# Global instance
neo4j_service = Neo4jService()

