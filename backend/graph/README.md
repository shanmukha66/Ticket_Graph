# Graph Module - Neo4j + GDS

Graph database operations for ticket management and community detection using Neo4j and Graph Data Science.

## Quick Start

### 1. Setup Database

```python
from backend.graph.build_graph import Neo4jGraph

# Initialize and setup schema
with Neo4jGraph() as graph:
    graph.setup_constraints()
    print("Database schema ready!")
```

### 2. Load Tickets and Sections

```python
with Neo4jGraph() as graph:
    # Batch load tickets
    tickets = [
        {
            'id': 'PROJ-1',
            'project': 'PROJECT',
            'priority': 'High',
            'status': 'Open',
            'summary': 'Login issue',
            'description': 'Users cannot login...',
            # ... other fields
        },
        # ... more tickets
    ]
    count = graph.batch_upsert_tickets(tickets)
    print(f"Loaded {count} tickets")
    
    # Batch load sections
    sections = [
        {
            'id': 'PROJ-1-summary',
            'key': 'summary',
            'text': 'Login issue',
            'ticket_id': 'PROJ-1'
        },
        {
            'id': 'PROJ-1-description',
            'key': 'description',
            'text': 'Users cannot login...',
            'ticket_id': 'PROJ-1'
        },
        # ... more sections
    ]
    count = graph.batch_upsert_sections(sections)
    print(f"Loaded {count} sections")
```

### 3. Generate Embeddings and Create Similarities

```python
from sentence_transformers import SentenceTransformer
from backend.graph.build_graph import connect_similar_tickets
import numpy as np

# Load embedding model
model = SentenceTransformer('sentence-transformers/e5-base-v2')

with Neo4jGraph() as graph:
    # Get all tickets with sections
    query = """
    MATCH (t:Ticket)
    OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
    RETURN t.id AS ticket_id, collect(s.text) AS texts
    """
    results = graph.execute_query(query)
    
    # Generate embeddings
    embeddings = {}
    for record in results:
        ticket_id = record['ticket_id']
        texts = [t for t in record['texts'] if t]
        
        if texts:
            combined_text = ' '.join(texts)
            embedding = model.encode(combined_text)
            embeddings[ticket_id] = embedding
    
    # Create similarity edges
    count = connect_similar_tickets(
        graph,
        embeddings,
        threshold=0.7,  # 70% similarity
        top_k=10        # Max 10 connections per ticket
    )
    print(f"Created {count} similarity edges")
```

### 4. Run Community Detection

```python
from backend.graph.community import CommunityDetector

with Neo4jGraph() as graph:
    detector = CommunityDetector(graph)
    
    # Run full analysis
    results = detector.get_full_analysis(
        algorithm='louvain',  # or 'leiden'
        top_tickets_per_community=3
    )
    
    # Print results
    print(f"\nFound {results['num_communities']} communities")
    print(f"Statistics: {results['statistics']}")
    
    for comm in results['communities']:
        print(f"\n{'='*60}")
        print(f"Community {comm['community_id']}: {comm['size']} tickets")
        print(f"Reason: {comm['reason']}")
        print(f"Top tickets:")
        for ticket in comm['top_tickets']:
            print(f"  - {ticket['id']}: {ticket['summary']}")
```

### 5. Query Context for RAG

```python
with Neo4jGraph() as graph:
    # Get ticket with similar tickets and sections
    query = """
    MATCH (t:Ticket {id: $ticket_id})
    OPTIONAL MATCH (t)-[:HAS_SECTION]->(ts:Section)
    OPTIONAL MATCH (t)-[sim:SIMILAR_TO]->(st:Ticket)
    WHERE sim.score >= $threshold
    OPTIONAL MATCH (st)-[:HAS_SECTION]->(ss:Section)
    RETURN t,
           collect(DISTINCT ts) AS ticket_sections,
           collect(DISTINCT {
               ticket: st,
               score: sim.score,
               sections: collect(DISTINCT ss)
           }) AS similar_tickets
    LIMIT $max_similar
    """
    
    context = graph.execute_query(query, {
        'ticket_id': 'PROJ-123',
        'threshold': 0.7,
        'max_similar': 5
    })
    
    # Use context for RAG response generation
    if context:
        ticket = context[0]['t']
        sections = context[0]['ticket_sections']
        similar = context[0]['similar_tickets']
        
        print(f"Ticket: {ticket['summary']}")
        print(f"Found {len(similar)} similar tickets")
```

## Module Structure

```
graph/
├── __init__.py
├── README.md                    # This file
├── build_graph.py              # Neo4jGraph class
├── community.py                # CommunityDetector class
└── cypher/
    ├── constraints.cypher      # Schema setup
    ├── queries.cypher          # Parameterized queries
    └── gds.cypher             # GDS algorithms
```

## API Reference

### Neo4jGraph Class

**Connection**
- `connect()` - Establish connection
- `close()` - Close connection
- Context manager support: `with Neo4jGraph() as graph:`

**Schema**
- `setup_constraints()` - Run constraints.cypher
- `run_cypher_file(filename)` - Execute .cypher file

**Ticket Operations**
- `upsert_ticket(ticket_data)` - Create/update single ticket
- `batch_upsert_tickets(tickets)` - Bulk upsert tickets
- `get_ticket_with_sections(ticket_id)` - Fetch ticket + sections

**Section Operations**
- `upsert_section(section_id, key, text, ticket_id)` - Create/update section
- `batch_upsert_sections(sections)` - Bulk upsert sections

**Similarity**
- `create_similarity_edges(similarities, method)` - Create SIMILAR_TO edges
- `connect_similar_tickets(graph, embeddings, threshold, top_k)` - Helper function

**Utilities**
- `execute_query(query, parameters)` - Run parameterized query
- `get_stats()` - Database statistics

### CommunityDetector Class

**Detection**
- `run_louvain(graph_name, write)` - Louvain algorithm
- `run_leiden(graph_name, write, gamma, theta)` - Leiden algorithm

**Analysis**
- `get_community_stats()` - Sizes and statistics
- `get_community_members(community_id)` - All tickets in community
- `get_top_tickets_per_community(top_n)` - Representative tickets
- `analyze_community_text(community_id, top_terms)` - Frequent terms
- `generate_community_summary(community_id)` - Full summary
- `get_full_analysis(algorithm, top_tickets_per_community)` - Complete workflow

**Utilities**
- `drop_projection(graph_name)` - Clean up GDS projection

## Cypher Files

### constraints.cypher
- Uniqueness: `Ticket(id)`, `Section(id)`
- Indexes: `Ticket(project, issueType, status)`, `Section(key)`

### queries.cypher
- Ticket CRUD operations
- Section management
- Similarity edge creation
- Subgraph queries (1-hop, N-hop, context)
- Utility queries

### gds.cypher
- Graph projections
- Louvain/Leiden community detection
- PageRank (optional)
- FastRP node embeddings (optional)
- Community analysis queries

## Environment Variables

Set in `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

## Common Patterns

### Pattern 1: Bulk Load from CSV/JSON

```python
import json
from backend.graph.build_graph import Neo4jGraph

with open('tickets.jsonl', 'r') as f:
    tickets = [json.loads(line) for line in f]

with Neo4jGraph() as graph:
    # Load in batches
    batch_size = 100
    for i in range(0, len(tickets), batch_size):
        batch = tickets[i:i+batch_size]
        count = graph.batch_upsert_tickets(batch)
        print(f"Loaded batch {i//batch_size + 1}: {count} tickets")
```

### Pattern 2: Incremental Similarity Updates

```python
from backend.graph.build_graph import Neo4jGraph
import numpy as np

with Neo4jGraph() as graph:
    # Get tickets without similarities
    query = """
    MATCH (t:Ticket)
    WHERE NOT (t)-[:SIMILAR_TO]-()
    RETURN t.id AS id
    LIMIT 100
    """
    tickets = graph.execute_query(query)
    
    # Generate embeddings and similarities for these tickets
    # ... (embedding code)
    
    # Create edges
    count = graph.create_similarity_edges(similarities)
    print(f"Added {count} new similarity edges")
```

### Pattern 3: Community-Aware Search

```python
with Neo4jGraph() as graph:
    # Find tickets in same community
    query = """
    MATCH (t1:Ticket {id: $ticket_id})
    MATCH (t2:Ticket {communityId: t1.communityId})
    WHERE t1 <> t2
    OPTIONAL MATCH (t2)-[:HAS_SECTION]->(s:Section)
    RETURN t2, collect(s) AS sections
    LIMIT $limit
    """
    
    related = graph.execute_query(query, {
        'ticket_id': 'PROJ-123',
        'limit': 10
    })
```

## Troubleshooting

**Connection Issues**
```python
# Test connection
from backend.graph.build_graph import Neo4jGraph

try:
    graph = Neo4jGraph()
    graph.connect()
    print("✓ Connected successfully")
    graph.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

**GDS Not Available**
```python
# Check GDS installation
with Neo4jGraph() as graph:
    try:
        result = graph.execute_query("RETURN gds.version() AS version")
        print(f"GDS version: {result[0]['version']}")
    except:
        print("GDS plugin not installed")
```

**Memory Issues with Large Graphs**
- Use batch processing
- Limit similarity top_k
- Drop projections when done
- Use sampling for initial testing

## Best Practices

1. **Always use context managers** for automatic cleanup
2. **Batch operations** for performance (100-1000 records per batch)
3. **Set similarity thresholds** carefully (0.6-0.8 typically works well)
4. **Limit top_k** to avoid creating too many edges (5-20 recommended)
5. **Drop GDS projections** after use to free memory
6. **Use indexes** - run constraints.cypher first
7. **Monitor query performance** with EXPLAIN/PROFILE in Neo4j Browser

## Examples Repository

See `PHASE2_COMPLETE.md` for comprehensive examples and usage patterns.

