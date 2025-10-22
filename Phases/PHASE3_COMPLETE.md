# Phase 3 — Ingestion + Embeddings + Vector Index ✅

## Completed Tasks

### 1. Created `backend/ingestors/schema_template.yml` ✅
**Purpose**: Define standardized section keys for ticket data decomposition

**Section Keys Defined**:
- `issue_summary` - Brief one-line summary
- `issue_description` - Detailed description
- `steps_to_reproduce` - Reproduction steps
- `root_cause` - Root cause analysis
- `resolution` - How the issue was resolved
- `priority` - Priority level and justification
- `comments` - Comments and discussion (multiple allowed)

**Features**:
- Field mappings for JIRA, CSV, and JSONL formats
- Preprocessing rules (min/max length, HTML stripping, whitespace normalization)
- Source field alternatives for flexible data parsing

---

### 2. Created `backend/retrieval/embedder.py` ✅
**Purpose**: E5 embedding service with L2 normalization

**Features**:

#### Embedder Class
```python
class Embedder:
    - load() - Load sentence-transformers E5 model
    - embed_text() - Single text embedding
    - embed_texts() - Batch text embeddings
    - embed_query() - Optimized for search queries
    - embed_documents() - Optimized for documents
```

**Key Characteristics**:
- Uses `sentence-transformers/e5-base-v2` by default (768 dimensions)
- Automatic L2 normalization for cosine similarity
- E5-specific prefixes: "query: " for queries, "passage: " for documents
- Batch processing with configurable batch size
- Progress bar support for long operations

**Usage**:
```python
from backend.retrieval.embedder import Embedder

embedder = Embedder()
embedder.load()

# Single text
embedding = embedder.embed_text("Hello world", normalize=True)

# Batch documents
embeddings = embedder.embed_documents(
    ["doc1", "doc2", "doc3"],
    batch_size=32,
    show_progress=True
)

# Query embedding
query_emb = embedder.embed_query("search query")
```

---

### 3. Created `backend/retrieval/vector_store.py` ✅
**Purpose**: FAISS-based vector store with Inner Product for cosine similarity

**Features**:

#### VectorStore Class
```python
class VectorStore:
    - add(texts, embeddings, metadatas) - Add vectors
    - search(query_embedding, k, min_score) - K-NN search
    - search_batch(query_embeddings, k) - Batch search
    - persist() - Save to disk
    - load() - Load from disk
    - clear() - Clear all data
    - get_by_ticket(ticket_id) - Get all sections for a ticket
    - get_stats() - Statistics
```

**Technical Details**:
- Uses `IndexFlatIP` (Inner Product) for exact similarity
- Requires L2-normalized vectors (IP = cosine similarity)
- Stores parallel metadata (ticket_id, section_key, text)
- Persistence via FAISS + pickle
- Efficient batch operations

**Metadata Structure**:
```python
{
    'ticket_id': 'PROJ-123',
    'section_key': 'issue_summary',
    'section_id': 'PROJ-123_issue_summary',
    'text': '...'
}
```

**Usage**:
```python
from backend.retrieval.vector_store import VectorStore

store = VectorStore(dimension=768)

# Add vectors
store.add(
    texts=["text1", "text2"],
    embeddings=np.array([[...], [...]]),  # L2-normalized
    metadatas=[
        {'ticket_id': 'T1', 'section_key': 'summary'},
        {'ticket_id': 'T2', 'section_key': 'description'}
    ]
)

# Search
results = store.search(query_embedding, k=5, min_score=0.7)
# Returns: [{'text': '...', 'metadata': {...}, 'score': 0.85, 'index': 42}]

# Persist
store.persist()  # Saves to FAISS_INDEX_PATH

# Load
store.load()
```

---

### 4. Created `backend/ingestors/load_csv.py` ✅
**Purpose**: Ingest JIRA tickets from CSV format

**Features**:
- Reads CSV from `CSV_PATH` env variable (default: `/mnt/data/jira_issues_clean.csv`)
- Maps columns to schema template keys
- Extracts multiple sections per ticket
- Batch operations for Neo4j (configurable batch size)
- Generates embeddings for all sections
- Adds embeddings to FAISS with metadata
- Persists vector store

**Column Mappings**:
```python
{
    'Issue key': ticket_id,
    'Project key': project,
    'Priority': priority,
    'Status': status,
    'Issue Type': issueType,
    'Summary': summary,
    'Description': description,
    'Created': created,
    'Updated': updated,
    'Reporter': reporter,
    'Assignee': assignee
}
```

**Usage**:
```python
from backend.ingestors.load_csv import ingest_csv

stats = ingest_csv(
    csv_path='/path/to/file.csv',
    batch_size=100,
    max_rows=1000  # For testing
)

# Returns:
# {
#     'tickets_loaded': 1000,
#     'sections_loaded': 5432,
#     'embeddings_generated': 5432,
#     'errors': 3
# }
```

**CLI Usage**:
```bash
python -m backend.ingestors.load_csv /path/to/file.csv 100
```

---

### 5. Created `backend/ingestors/load_jsonl.py` ✅
**Purpose**: Ingest JIRA tickets from JSONL format

**Features**:
- Reads JSONL from `JSONL_PATH` env variable (default: `/mnt/data/jira_issues_rag.jsonl`)
- Flexible JSON field extraction
- Handles nested structures and lists
- Supports multiple comments per ticket
- Same batch processing as CSV ingestion
- Generates embeddings and updates vector store

**JSON Field Mappings**:
```python
{
    'issue_key' or 'id' or 'key': ticket_id,
    'project': project,
    'priority': priority,
    'status': status,
    'issue_type' or 'type': issueType,
    'summary': summary,
    'description': description,
    'comments': [comment1, comment2, ...]  # Multiple sections
}
```

**Usage**:
```python
from backend.ingestors.load_jsonl import ingest_jsonl

stats = ingest_jsonl(
    jsonl_path='/path/to/file.jsonl',
    batch_size=100,
    max_rows=1000
)
```

**CLI Usage**:
```bash
python -m backend.ingestors.load_jsonl /path/to/file.jsonl 100
```

---

### 6. Created `ingest_all()` Function ✅
**Purpose**: Complete end-to-end ingestion pipeline

**Location**: `backend/ingestors/__init__.py`

**Pipeline Steps**:
1. **Setup Neo4j constraints** - Run constraints.cypher
2. **Load CSV** - Ingest tickets, sections, embeddings from CSV
3. **Load JSONL** - Ingest tickets, sections, embeddings from JSONL
4. **Build similarity edges** - Create SIMILAR_TO relationships using embeddings
5. **Run community detection** - Detect communities and store communityId

**Features**:
- Graceful handling of missing files
- Automatic embedding aggregation per ticket
- Configurable similarity threshold and top-k
- Choice of Louvain or Leiden algorithm
- Comprehensive statistics tracking
- Progress reporting

**Usage**:
```python
from backend.ingestors import ingest_all

stats = ingest_all(
    csv_path='/path/to/csv',  # Optional, uses env default
    jsonl_path='/path/to/jsonl',  # Optional, uses env default
    similarity_threshold=0.7,  # 70% cosine similarity
    similarity_top_k=10,  # Max 10 connections per ticket
    community_algorithm='louvain'  # or 'leiden'
)

# Returns:
# {
#     'csv_tickets': 500,
#     'csv_sections': 2500,
#     'jsonl_tickets': 1500,
#     'jsonl_sections': 7500,
#     'total_tickets': 2000,
#     'total_sections': 10000,
#     'similarity_edges': 15000,
#     'communities': 25
# }
```

**CLI Usage**:
```bash
# From Python
python -c "from backend.ingestors import ingest_all; ingest_all()"

# Or create a script
cat > ingest.py << 'SCRIPT'
from backend.ingestors import ingest_all
stats = ingest_all()
print(f"\nIngestion complete!")
print(f"Total tickets: {stats['total_tickets']}")
print(f"Total sections: {stats['total_sections']}")
print(f"Similarity edges: {stats['similarity_edges']}")
print(f"Communities: {stats['communities']}")
SCRIPT

python ingest.py
```

---

## File Structure

```
backend/
├── ingestors/
│   ├── __init__.py              ✅ ingest_all() function
│   ├── schema_template.yml      ✅ Section schema definition
│   ├── load_csv.py              ✅ CSV ingestion
│   └── load_jsonl.py            ✅ JSONL ingestion
│
├── retrieval/
│   ├── __init__.py
│   ├── embedder.py              ✅ E5 embedding service
│   └── vector_store.py          ✅ FAISS vector store
│
├── graph/
│   ├── build_graph.py           (from Phase 2)
│   ├── community.py             (from Phase 2)
│   └── cypher/                  (from Phase 2)
│
└── utils/
    └── env.py                   (from Phase 1)
```

---

## Complete Workflow Example

### Step 1: Setup Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env
nano .env
```

Edit `.env`:
```bash
EMBED_MODEL=sentence-transformers/e5-base-v2
FAISS_INDEX_PATH=./faiss_index
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
CSV_PATH=/mnt/data/jira_issues_clean.csv
JSONL_PATH=/mnt/data/jira_issues_rag.jsonl
```

### Step 2: Start Neo4j

```bash
# Using Docker
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -e NEO4J_PLUGINS='["graph-data-science"]' \
  neo4j:latest

# Wait for Neo4j to start
sleep 30
```

### Step 3: Run Complete Ingestion

```python
from backend.ingestors import ingest_all

# Run complete pipeline
stats = ingest_all(
    similarity_threshold=0.7,
    similarity_top_k=10,
    community_algorithm='louvain'
)

print("\n" + "="*70)
print("INGESTION PIPELINE RESULTS")
print("="*70)
print(f"CSV tickets: {stats['csv_tickets']}")
print(f"CSV sections: {stats['csv_sections']}")
print(f"JSONL tickets: {stats['jsonl_tickets']}")
print(f"JSONL sections: {stats['jsonl_sections']}")
print(f"Total tickets: {stats['total_tickets']}")
print(f"Total sections: {stats['total_sections']}")
print(f"Similarity edges: {stats['similarity_edges']}")
print(f"Communities detected: {stats['communities']}")
print("="*70)
```

### Step 4: Verify Data

```python
from backend.graph.build_graph import Neo4jGraph
from backend.retrieval.vector_store import VectorStore

# Check Neo4j
with Neo4jGraph() as graph:
    stats = graph.get_stats()
    print("\nNeo4j Statistics:")
    print(f"  Tickets: {stats['nodes'].get('Ticket', 0)}")
    print(f"  Sections: {stats['nodes'].get('Section', 0)}")
    print(f"  SIMILAR_TO edges: {stats['relationships'].get('SIMILAR_TO', 0)}")
    print(f"  HAS_SECTION edges: {stats['relationships'].get('HAS_SECTION', 0)}")

# Check FAISS
vector_store = VectorStore()
vector_store.load()
stats = vector_store.get_stats()
print("\nFAISS Vector Store:")
print(f"  Total vectors: {stats['total_vectors']}")
print(f"  Unique tickets: {stats['unique_tickets']}")
print(f"  Dimension: {stats['dimension']}")
print(f"  Section keys: {stats['section_keys']}")
```

### Step 5: Test Search

```python
from backend.retrieval.embedder import Embedder
from backend.retrieval.vector_store import VectorStore

# Load services
embedder = Embedder()
embedder.load()

vector_store = VectorStore()
vector_store.load()

# Search
query = "authentication login issue"
query_embedding = embedder.embed_query(query)
results = vector_store.search(query_embedding, k=5)

print(f"\nSearch results for: '{query}'")
for i, result in enumerate(results, 1):
    print(f"\n{i}. Score: {result['score']:.3f}")
    print(f"   Ticket: {result['metadata']['ticket_id']}")
    print(f"   Section: {result['metadata']['section_key']}")
    print(f"   Text: {result['text'][:100]}...")
```

### Step 6: Query Graph Context

```python
from backend.graph.build_graph import Neo4jGraph

with Neo4jGraph() as graph:
    # Get ticket with similar tickets
    query = """
    MATCH (t:Ticket {id: $ticket_id})
    OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
    OPTIONAL MATCH (t)-[sim:SIMILAR_TO]->(similar:Ticket)
    WHERE sim.score >= 0.7
    OPTIONAL MATCH (similar)-[:HAS_SECTION]->(sim_sec:Section)
    RETURN t.id AS ticket_id,
           t.summary AS summary,
           collect(DISTINCT s.text) AS sections,
           collect(DISTINCT {
               id: similar.id,
               summary: similar.summary,
               score: sim.score,
               sections: collect(DISTINCT sim_sec.text)
           }) AS similar_tickets
    LIMIT 1
    """
    
    result = graph.execute_query(query, {'ticket_id': 'YOUR-TICKET-ID'})
    
    if result:
        print(f"\nTicket: {result[0]['ticket_id']}")
        print(f"Summary: {result[0]['summary']}")
        print(f"\nSections: {len(result[0]['sections'])}")
        print(f"Similar tickets: {len(result[0]['similar_tickets'])}")
```

---

## Configuration

### Environment Variables (.env)

```bash
# Embedding model
EMBED_MODEL=sentence-transformers/e5-base-v2

# Vector store path
FAISS_INDEX_PATH=./faiss_index

# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Data paths
CSV_PATH=/mnt/data/jira_issues_clean.csv
JSONL_PATH=/mnt/data/jira_issues_rag.jsonl
```

### Ingestion Parameters

```python
ingest_all(
    csv_path=None,  # Use env CSV_PATH
    jsonl_path=None,  # Use env JSONL_PATH
    similarity_threshold=0.7,  # 70% cosine similarity
    similarity_top_k=10,  # Max 10 edges per ticket
    community_algorithm='louvain'  # or 'leiden'
)
```

**Recommended Settings**:
- `similarity_threshold`: 0.6-0.8 (lower = more edges, higher = more selective)
- `similarity_top_k`: 5-20 (balance between connectivity and performance)
- `community_algorithm`: 'louvain' (faster) or 'leiden' (more accurate)

---

## Performance Notes

### Embedding Generation
- E5-base-v2: ~768 dimensions, ~500MB model
- Speed: ~100-200 texts/second on CPU
- First load downloads model (~2-3 minutes)

### FAISS Indexing
- IndexFlatIP: Exact search, no approximation
- Linear time: O(n) for n vectors
- Suitable for up to ~1M vectors on single machine
- For larger scale, consider IndexIVFFlat or IndexHNSW

### Neo4j Ingestion
- Batch size 100-500 optimal for most cases
- ~1000-5000 tickets/second with batching
- Similarity edge creation is O(n²) with optimizations

### Memory Requirements
- Embeddings: 768 * 4 bytes * n_sections (~3KB per section)
- FAISS index: ~3KB per vector
- Neo4j: Varies, typically 1-10GB for 100K tickets

---

## Troubleshooting

### Issue: Out of Memory During Embedding
**Solution**: Reduce batch_size in ingestion functions
```python
ingest_csv(batch_size=50)  # Instead of default 100
```

### Issue: FAISS Index Not Found
**Solution**: Ensure FAISS_INDEX_PATH is writable
```bash
mkdir -p ./faiss_index
chmod 777 ./faiss_index
```

### Issue: Neo4j Connection Refused
**Solution**: Check Neo4j is running
```bash
docker ps | grep neo4j
# Or
neo4j status
```

### Issue: Slow Similarity Edge Creation
**Solution**: Reduce similarity_top_k or increase threshold
```python
ingest_all(similarity_threshold=0.75, similarity_top_k=5)
```

---

## Next Steps

Phase 3 is complete! The system now has:
✅ Complete data ingestion pipeline
✅ E5 embeddings for semantic search
✅ FAISS vector store for efficient retrieval
✅ Graph similarity edges
✅ Community detection

Ready for:
- **Phase 4**: RAG query pipeline and answer generation
- **Phase 5**: FastAPI endpoints
- **Phase 6**: Frontend integration

Phase 3 Complete! 🎉
