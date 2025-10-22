# Phase 2 — Graph Database (Neo4j + GDS) ✅

## Completed Tasks

### 1. Created `backend/graph/cypher/constraints.cypher` ✅
**Purpose**: Database schema setup with constraints and indexes

**Features**:
- Uniqueness constraints on `Ticket(id)` and `Section(id)`
- Indexes for efficient querying:
  - `Ticket(project)`, `Ticket(issueType)`, `Ticket(status)`
  - `Section(key)`
  - Composite index on `Ticket(project, status)`
- Optional full-text search indexes (commented)

**Usage**:
```python
graph = Neo4jGraph()
graph.connect()
graph.setup_constraints()
```

---

### 2. Created `backend/graph/cypher/queries.cypher` ✅
**Purpose**: Parameterized Cypher queries for graph operations

**Query Categories**:

#### Ticket Operations
- `upsert_ticket` - Create or update ticket with all properties
- `get_ticket` - Fetch single ticket by ID
- `get_tickets_by_project` - Get all tickets in a project

#### Section Operations
- `upsert_section` - Create section and attach to ticket via `[:HAS_SECTION]`
- `attach_section` - Link existing section to ticket
- `get_ticket_sections` - Fetch all sections for a ticket

#### Similarity Edges
- `create_similarity_edge` - Create `[:SIMILAR_TO {score}]` relationship
- `get_similar_tickets` - Find similar tickets with score threshold
- `batch_create_similarities` - Bulk create similarity edges

#### Subgraph Queries
- `get_subgraph_1hop` - 1-hop neighborhood around tickets
- `get_subgraph_nhop` - N-hop neighborhood (parameterized)
- `get_subgraph_with_sections` - Tickets + sections + similarities
- `get_context_subgraph` - Full context for RAG (ticket + sections + similar tickets + their sections)

#### Utility Queries
- `count_nodes` - Count by label
- `count_relationships` - Count by type
- `clear_similarities` - Remove all SIMILAR_TO edges
- `delete_all` - Clear entire graph

---

### 3. Created `backend/graph/cypher/gds.cypher` ✅
**Purpose**: Neo4j Graph Data Science algorithm queries

**Features**:

#### Graph Projections
- `project_ticket_graph` - Tickets connected by SIMILAR_TO (weighted, undirected)
- `project_ticket_section_graph` - Full graph with tickets + sections
- `drop_projection` - Clean up projections

#### Louvain Community Detection
- `louvain_stream` - Stream results without writing to graph
- `louvain_write` - Run and write `communityId` to nodes
- `louvain_stats` - Get statistics (modularity, community count)

#### Leiden Community Detection
- `leiden_stream` - Stream Leiden results (more accurate than Louvain)
- `leiden_write` - Write Leiden `communityId` to nodes
- Configurable gamma and theta parameters

#### PageRank (Optional)
- `pagerank_stream` - Identify important tickets
- `pagerank_write` - Write PageRank scores to nodes

#### Node Embeddings (Optional)
- `fastrp_stream` - Generate node embeddings using FastRP
- `fastrp_write` - Write embeddings to nodes

#### Community Analysis Queries
- `get_community_sizes` - Size of each community
- `get_community_members` - All tickets in a community with sections
- `get_top_tickets_per_community` - Representative tickets per cluster
- `get_community_text` - All section text for term frequency analysis
- `community_connectivity` - Internal vs external edge analysis

#### Cleanup
- `remove_community_ids` - Clear all communityId properties
- `remove_pagerank` - Clear PageRank scores

---

### 4. Implemented `backend/graph/build_graph.py` ✅
**Purpose**: Neo4jGraph class for graph operations and batch processing

**Features**:

#### Neo4jGraph Class
```python
class Neo4jGraph:
    - connect() / close() - Connection management
    - run_cypher_file() - Execute .cypher files
    - setup_constraints() - Run constraints.cypher
    - execute_query() - Run parameterized queries
    - upsert_ticket() - Create/update single ticket
    - upsert_section() - Create/update section with HAS_SECTION link
    - batch_upsert_tickets() - Bulk insert tickets
    - batch_upsert_sections() - Bulk insert sections
    - create_similarity_edges() - Create SIMILAR_TO relationships
    - get_ticket_with_sections() - Fetch ticket + sections
    - get_stats() - Database statistics
```

**Context Manager Support**:
```python
with Neo4jGraph() as graph:
    graph.setup_constraints()
    graph.upsert_ticket(ticket_data)
```

#### Helper Function: `connect_similar_tickets()`
**Purpose**: Create similarity edges using cosine similarity on embeddings

**Parameters**:
- `graph`: Neo4jGraph instance
- `ticket_embeddings`: Dict[ticket_id → embedding vector]
- `threshold`: Minimum cosine similarity (0-1)
- `top_k`: Max connections per ticket

**Algorithm**:
1. Compute pairwise cosine similarities
2. Filter by threshold
3. Keep top-k per ticket
4. Batch create SIMILAR_TO edges

**Usage**:
```python
embeddings = {
    'TICKET-1': np.array([0.1, 0.2, ...]),
    'TICKET-2': np.array([0.3, 0.4, ...]),
}
count = connect_similar_tickets(graph, embeddings, threshold=0.7, top_k=10)
```

---

### 5. Implemented `backend/graph/community.py` ✅
**Purpose**: Community detection with GDS and analysis

**Features**:

#### CommunityDetector Class
```python
class CommunityDetector:
    - __init__(graph: Neo4jGraph)
    - run_louvain() - Louvain algorithm with modularity optimization
    - run_leiden() - Leiden algorithm (falls back to Louvain if unavailable)
    - get_community_stats() - Sizes, counts, avg/min/max
    - get_community_members() - All tickets in a community
    - get_top_tickets_per_community() - Representative tickets by degree
    - analyze_community_text() - Extract frequent terms
    - generate_community_summary() - Full summary with reasons
    - get_full_analysis() - Complete analysis with all communities
```

#### Key Methods

**run_louvain() / run_leiden()**
- Ensures graph projection exists
- Runs GDS algorithm
- Writes `communityId` to nodes
- Returns community count and modularity

**generate_community_summary()**
Returns:
```json
{
  "community_id": 42,
  "size": 157,
  "top_tickets": [
    {"id": "PROJ-123", "summary": "...", "degree": 15},
    {"id": "PROJ-456", "summary": "...", "degree": 12}
  ],
  "frequent_terms": ["authentication", "login", "session", "token", ...],
  "reason": "Common themes: authentication, login, session, token, security"
}
```

**get_full_analysis()**
Complete community detection workflow:
1. Run Louvain/Leiden
2. Compute statistics
3. Analyze each community
4. Extract frequent terms
5. Select representative tickets
6. Generate human-readable reasons

Returns:
```json
{
  "algorithm": "louvain",
  "num_communities": 12,
  "cluster_sizes": {0: 45, 1: 38, 2: 67, ...},
  "statistics": {...},
  "communities": [
    {
      "community_id": 0,
      "size": 45,
      "top_tickets": [...],
      "frequent_terms": [...],
      "reason": "Common themes: ..."
    },
    ...
  ]
}
```

---

## File Structure

```
backend/
├── graph/
│   ├── __init__.py
│   ├── build_graph.py              ✅ Neo4jGraph class + similarity helper
│   ├── community.py                ✅ CommunityDetector class
│   └── cypher/
│       ├── __init__.py
│       ├── constraints.cypher      ✅ Schema constraints & indexes
│       ├── queries.cypher          ✅ Parameterized queries
│       └── gds.cypher              ✅ GDS algorithms & projections
```

---

## Usage Examples

### 1. Setup Database Schema
```python
from backend.graph.build_graph import Neo4jGraph

with Neo4jGraph() as graph:
    graph.setup_constraints()
```

### 2. Upsert Tickets and Sections
```python
with Neo4jGraph() as graph:
    # Single ticket
    ticket = graph.upsert_ticket({
        'id': 'PROJ-123',
        'project': 'PROJECT',
        'priority': 'High',
        'status': 'Open',
        'summary': 'Fix login bug',
        'description': 'Users cannot log in...'
    })
    
    # Batch tickets
    tickets = [...]  # List of ticket dicts
    count = graph.batch_upsert_tickets(tickets)
    
    # Add sections
    sections = [
        {
            'id': 'PROJ-123-summary',
            'key': 'summary',
            'text': 'Fix login bug',
            'ticket_id': 'PROJ-123'
        },
        {
            'id': 'PROJ-123-desc',
            'key': 'description',
            'text': 'Users cannot log in...',
            'ticket_id': 'PROJ-123'
        }
    ]
    count = graph.batch_upsert_sections(sections)
```

### 3. Create Similarity Edges
```python
from backend.graph.build_graph import connect_similar_tickets
import numpy as np

# Assume embeddings generated from sections
embeddings = {
    'PROJ-123': np.array([...]),
    'PROJ-456': np.array([...]),
}

with Neo4jGraph() as graph:
    count = connect_similar_tickets(
        graph,
        embeddings,
        threshold=0.7,
        top_k=10
    )
    print(f"Created {count} similarity edges")
```

### 4. Run Community Detection
```python
from backend.graph.build_graph import Neo4jGraph
from backend.graph.community import CommunityDetector

with Neo4jGraph() as graph:
    detector = CommunityDetector(graph)
    
    # Full analysis
    results = detector.get_full_analysis(algorithm='louvain')
    
    print(f"Found {results['num_communities']} communities")
    
    for comm in results['communities']:
        print(f"\nCommunity {comm['community_id']}: {comm['size']} tickets")
        print(f"  Reason: {comm['reason']}")
        print(f"  Top tickets:")
        for t in comm['top_tickets']:
            print(f"    - {t['id']}: {t['summary']}")
```

### 5. Query Context for RAG
```python
with Neo4jGraph() as graph:
    query = """
    MATCH (t:Ticket {id: $ticket_id})
    OPTIONAL MATCH (t)-[:HAS_SECTION]->(ts:Section)
    OPTIONAL MATCH (t)-[sim:SIMILAR_TO]->(st:Ticket)
    WHERE sim.score >= $similarity_threshold
    WITH t, collect(ts) AS sections, 
         collect({ticket: st, score: sim.score}) AS similar
         LIMIT $max_similar
    RETURN t, sections, similar
    """
    
    context = graph.execute_query(query, {
        'ticket_id': 'PROJ-123',
        'similarity_threshold': 0.7,
        'max_similar': 5
    })
```

---

## Integration with Embeddings

The graph module is designed to work with embedding services:

```python
from backend.graph.build_graph import Neo4jGraph, connect_similar_tickets
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer('sentence-transformers/e5-base-v2')

# Get tickets with sections
with Neo4jGraph() as graph:
    tickets = graph.execute_query("MATCH (t:Ticket) RETURN t LIMIT 100")
    
    embeddings = {}
    for record in tickets:
        ticket_id = record['t']['id']
        
        # Get sections
        sections = graph.execute_query(
            "MATCH (t:Ticket {id: $id})-[:HAS_SECTION]->(s:Section) RETURN s.text",
            {'id': ticket_id}
        )
        
        # Combine section text
        text = ' '.join([s['s.text'] for s in sections])
        
        # Generate embedding
        embedding = model.encode(text)
        embeddings[ticket_id] = embedding
    
    # Create similarity edges
    count = connect_similar_tickets(graph, embeddings, threshold=0.7, top_k=10)
```

---

## Next Steps

Phase 2 is complete! The graph database infrastructure is ready for:

- **Phase 3**: Embedding generation and FAISS vector search
- **Phase 4**: RAG pipeline integration
- **Phase 5**: API endpoints and frontend integration

The system now supports:
✅ Efficient graph storage with proper indexing
✅ Batch operations for scalability
✅ Similarity-based ticket connections
✅ Community detection with GDS
✅ Context retrieval for RAG queries
✅ Representative ticket selection
✅ Term frequency analysis for cluster interpretation

Phase 2 Complete! 🚀
