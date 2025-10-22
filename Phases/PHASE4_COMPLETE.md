# Phase 4 — LLM Prompts + Dual Answers ✅

## Completed Tasks

### 1. Created `backend/llm/prompts.py` ✅
**Purpose**: Prompt templates for general and graph RAG answer generation

**Prompts Defined**:

#### GENERAL_PROMPT
- Help-desk style assistant for technical support
- Clear, concise, actionable answers
- Professional tone with structured responses
- No context required - general knowledge based

**Key Instructions**:
- Be clear and concise
- Focus on practical solutions
- Organize with sections/bullets
- Maintain professional, supportive tone

#### GRAPH_RAG_PROMPT
- Context-based answer with strict citation requirements
- Must reference specific ticket IDs
- Include community cluster insights
- Provide reasoning from graph relationships
- Structured response format

**Required Elements**:
1. **Answer ONLY from provided context**
2. **Cite specific tickets**: "According to PROJ-123..."
3. **Reference communities**: "Issues in Cluster #2..."
4. **Provide reasoning**: Explain WHY tickets are related
5. **Structured format**:
   - Direct Answer
   - Supporting Evidence (with citations)
   - Related Patterns (cluster insights)
   - Recommended Actions

**Context Structure**:
- Similar Sections: Relevant text from past tickets
- Graph Connections: Related tickets and relationships
- Community Clusters: Groups of similar issues
- Section Types: Different ticket aspects

#### Helper Functions
- `format_context_sections()` - Format retrieved sections for prompt
- `format_graph_info()` - Format graph analysis (nodes, edges, top tickets)
- `format_community_info()` - Format cluster summaries with themes
- `build_graph_rag_prompt()` - Assemble complete prompt with all context

---

### 2. Created `backend/llm/answer.py` ✅
**Purpose**: Answer generation functions using OpenAI with dual approaches

**Functions Implemented**:

#### answer_general(query, model="gpt-4")
**Purpose**: Generate general help-desk style answer without context

**Features**:
- Uses GENERAL_PROMPT template
- Direct OpenAI API call
- No context retrieval
- Fast, straightforward answers

**Returns**:
```python
{
    "answer": "...",
    "model": "gpt-4",
    "tokens": 450,
    "approach": "general"
}
```

**Usage**:
```python
from backend.llm.answer import answer_general

result = answer_general("How to fix login timeout?")
print(result['answer'])
```

---

#### retrieve_graph_context(query, top_k_sections=10, num_hops=1)
**Purpose**: Comprehensive graph context retrieval pipeline

**Pipeline Steps**:
1. **Vector Search**: Find top N relevant sections using FAISS
2. **Extract Ticket IDs**: Get unique tickets from sections
3. **Graph Expansion**: N-hop neighborhood via Neo4j with SIMILAR_TO edges
4. **Community Info**: Get cluster summaries and themes
5. **Rank & Organize**: Structure context for LLM consumption

**Parameters**:
- `query`: User question
- `top_k_sections`: Number of sections from vector search (default: 10)
- `num_hops`: Graph traversal depth (default: 1)
- `similarity_threshold`: Min edge score (default: 0.7)
- `max_similar_tickets`: Max connections per ticket (default: 5)

**Returns**:
```python
{
    "sections": [
        {
            "text": "...",
            "metadata": {
                "ticket_id": "PROJ-123",
                "section_key": "resolution",
                "section_id": "..."
            },
            "score": 0.85
        },
        ...
    ],
    
    "graph_context": {
        "num_similar": 12,
        "num_hops": 1,
        "num_nodes": 25,
        "num_relationships": 18,
        "top_tickets": [
            {
                "id": "PROJ-123",
                "summary": "Login timeout issue",
                "degree": 8
            },
            ...
        ],
        "seed_tickets": ["PROJ-123", "PROJ-456"],
        "all_tickets": [...],
        "similar_tickets": [...]
    },
    
    "community_context": [
        {
            "community_id": 2,
            "size": 45,
            "reason": "Common themes: authentication, login, session, timeout",
            "top_tickets": [...],
            "frequent_terms": ["authentication", "login", "session", ...]
        },
        ...
    ],
    
    "provenance": {
        "ticket_ids": ["PROJ-123", "PROJ-456", ...],
        "section_ids": [...],
        "community_ids": [2, 5],
        "num_sections": 10,
        "num_tickets": 8,
        "num_communities": 2
    }
}
```

**Neo4j Query Used**:
```cypher
MATCH (t:Ticket) WHERE t.id IN $ticket_ids
OPTIONAL MATCH (t)-[:HAS_SECTION]->(s:Section)
OPTIONAL MATCH (t)-[sim:SIMILAR_TO]->(similar:Ticket)
WHERE sim.score >= $threshold
OPTIONAL MATCH (similar)-[:HAS_SECTION]->(sim_sec:Section)
RETURN t, sections, similar_tickets, communityId
```

---

#### answer_graph_rag(query, top_k_sections=10, num_hops=1, model="gpt-4")
**Purpose**: Generate graph RAG answer with citations and provenance

**Complete Workflow**:
1. Retrieve graph context via `retrieve_graph_context()`
2. Build comprehensive prompt with all context
3. Call OpenAI with GRAPH_RAG_PROMPT
4. Extract and structure response
5. Return answer with full provenance

**Returns**:
```python
{
    "answer": "...",  # LLM-generated answer with citations
    
    "provenance": {
        "ticket_ids": ["PROJ-123", "PROJ-456"],
        "section_ids": [...],
        "community_ids": [2, 5],
        "num_sections": 10,
        "num_tickets": 8,
        "num_communities": 2
    },
    
    "model": "gpt-4",
    "tokens": 1200,
    "approach": "graph_rag",
    
    # Graph analysis details
    "clusters": [
        {
            "cluster_id": 2,
            "size": 45,
            "reason": "Common themes: authentication, login, session",
            "top_tickets": ["PROJ-123", "PROJ-456", "PROJ-789"]
        },
        ...
    ],
    
    "top_nodes": [
        {
            "id": "PROJ-123",
            "summary": "Login timeout issue",
            "degree": 8
        },
        ...
    ],
    
    "edges": {
        "total": 18,
        "threshold": 0.7,
        "description": "18 similarity connections used"
    },
    
    "reasoning": {
        "cluster_2": "Common themes: authentication, login, session",
        "cluster_5": "Common themes: api, integration, webhook"
    },
    
    "context_summary": {
        "sections_retrieved": 10,
        "tickets_involved": 8,
        "communities_analyzed": 2,
        "graph_nodes": 25,
        "graph_edges": 18
    }
}
```

**Usage**:
```python
from backend.llm.answer import answer_graph_rag

result = answer_graph_rag(
    "How to fix login timeout?",
    top_k_sections=10,
    num_hops=1,
    model="gpt-4"
)

print(result['answer'])
print(f"\nBased on {len(result['provenance']['ticket_ids'])} tickets")
print(f"Communities: {result['provenance']['community_ids']}")
print(f"\nClusters involved:")
for cluster in result['clusters']:
    print(f"  - Cluster {cluster['cluster_id']}: {cluster['reason']}")
```

---

#### answer_dual(query, model="gpt-4") [BONUS]
**Purpose**: Generate both approaches for comparison

**Returns**:
```python
{
    "query": "...",
    "general": {...},  # General answer result
    "graph_rag": {...},  # Graph RAG result
    "comparison": {
        "general_length": 450,
        "graph_rag_length": 980,
        "citations_count": 8,
        "communities_used": 2
    }
}
```

---

## File Structure

```
backend/
├── llm/
│   ├── __init__.py          ✅ Module exports
│   ├── prompts.py           ✅ Prompt templates & formatting
│   └── answer.py            ✅ Answer generation functions
│
├── retrieval/
│   ├── embedder.py          (from Phase 3)
│   └── vector_store.py      (from Phase 3)
│
├── graph/
│   ├── build_graph.py       (from Phase 2)
│   └── community.py         (from Phase 2)
│
└── requirements.txt         ✅ Added openai==1.3.7
```

---

## Complete Usage Examples

### Example 1: General Answer

```python
from backend.llm.answer import answer_general

# Simple, context-free answer
result = answer_general("How do I debug memory leaks in Python?")

print(result['answer'])
# Output:
# "Memory leaks in Python can be debugged using several approaches:
#  
#  1. **Use memory profiling tools**:
#     - memory_profiler module
#     - tracemalloc (built-in)
#     - objgraph for object references
#  
#  2. **Common causes**:
#     - Circular references
#     - Global variables
#     - Caching without limits
#  ..."

print(f"Model: {result['model']}")
print(f"Tokens: {result['tokens']}")
```

### Example 2: Graph RAG Answer

```python
from backend.llm.answer import answer_graph_rag

# Context-aware answer with citations
result = answer_graph_rag(
    "How to fix authentication timeout issues?",
    top_k_sections=10,
    num_hops=1
)

print(result['answer'])
# Output:
# "**Direct Answer**
#  Based on similar issues in the knowledge base, authentication timeout
#  problems typically stem from session configuration or token expiration.
#  
#  **Supporting Evidence**
#  According to PROJ-4523, increasing the session timeout from 30 to 60
#  minutes resolved the issue for most users. The ticket shows...
#  
#  PROJ-6721 and PROJ-7834 in Cluster #12 (authentication issues) indicate
#  that token refresh mechanisms should be implemented...
#  
#  **Related Patterns**
#  This is similar to issues in Cluster #12 (45 tickets), which share
#  common themes: authentication, session, timeout, token, refresh.
#  ..."

print(f"\nProvenance:")
print(f"  Tickets: {result['provenance']['ticket_ids']}")
print(f"  Communities: {result['provenance']['community_ids']}")

print(f"\nClusters involved:")
for cluster in result['clusters']:
    print(f"  Cluster {cluster['cluster_id']}: {cluster['reason']}")
    print(f"    Size: {cluster['size']} tickets")
    print(f"    Top: {', '.join(cluster['top_tickets'][:3])}")

print(f"\nTop connected nodes:")
for node in result['top_nodes'][:3]:
    print(f"  {node['id']}: {node['summary']} (degree: {node['degree']})")

print(f"\nEdges used: {result['edges']['total']} similarity connections")
```

### Example 3: Context Retrieval Only

```python
from backend.llm.answer import retrieve_graph_context

# Just get context without LLM call
context = retrieve_graph_context(
    "session management best practices",
    top_k_sections=15,
    num_hops=2
)

print(f"Retrieved {len(context['sections'])} sections")
print(f"From {len(context['provenance']['ticket_ids'])} tickets")
print(f"Involving {len(context['provenance']['community_ids'])} communities")

print("\nTop sections:")
for i, section in enumerate(context['sections'][:5], 1):
    print(f"\n{i}. {section['metadata']['ticket_id']} - {section['metadata']['section_key']}")
    print(f"   Score: {section['score']:.3f}")
    print(f"   Text: {section['text'][:100]}...")

print("\nCommunity insights:")
for comm in context['community_context']:
    print(f"\nCluster {comm['community_id']}: {comm['size']} tickets")
    print(f"  Theme: {comm['reason']}")
    print(f"  Terms: {', '.join(comm['frequent_terms'][:5])}")
```

### Example 4: Dual Comparison

```python
from backend.llm.answer import answer_dual

# Generate both answers
results = answer_dual("How to handle database connection pooling?")

print("="*70)
print("GENERAL ANSWER")
print("="*70)
print(results['general']['answer'])

print("\n" + "="*70)
print("GRAPH RAG ANSWER (with context)")
print("="*70)
print(results['graph_rag']['answer'])

print("\n" + "="*70)
print("COMPARISON")
print("="*70)
print(f"General length: {results['comparison']['general_length']} chars")
print(f"Graph RAG length: {results['comparison']['graph_rag_length']} chars")
print(f"Citations: {results['comparison']['citations_count']} tickets")
print(f"Communities: {results['comparison']['communities_used']} clusters")
```

---

## Graph RAG Answer Structure

The `answer_graph_rag()` function provides comprehensive metadata:

### 1. Clusters Involved
```python
result['clusters'] = [
    {
        "cluster_id": 2,
        "size": 45,
        "reason": "Common themes: authentication, login, session",
        "top_tickets": ["PROJ-123", "PROJ-456", "PROJ-789"]
    },
    ...
]
```

### 2. Top Nodes (Most Connected)
```python
result['top_nodes'] = [
    {
        "id": "PROJ-123",
        "summary": "Login timeout issue",
        "degree": 8  # Number of connections
    },
    ...
]
```

### 3. Edges Used
```python
result['edges'] = {
    "total": 18,
    "threshold": 0.7,
    "description": "18 similarity connections used"
}
```

### 4. Reasoning Per Cluster
```python
result['reasoning'] = {
    "cluster_2": "Common themes: authentication, login, session, timeout",
    "cluster_5": "Common themes: api, integration, webhook, callback"
}
```

### 5. Provenance (Traceability)
```python
result['provenance'] = {
    "ticket_ids": ["PROJ-123", "PROJ-456", ...],
    "section_ids": ["PROJ-123_resolution", ...],
    "community_ids": [2, 5],
    "num_sections": 10,
    "num_tickets": 8,
    "num_communities": 2
}
```

---

## Configuration

### Environment Variables

Add to `.env`:
```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-api-key-here

# Embedding Model (already set)
EMBED_MODEL=sentence-transformers/e5-base-v2

# FAISS Index Path (already set)
FAISS_INDEX_PATH=./faiss_index

# Neo4j (already set)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Function Parameters

```python
# General answer
answer_general(
    query="...",
    model="gpt-4"  # or "gpt-3.5-turbo" for faster/cheaper
)

# Graph RAG answer
answer_graph_rag(
    query="...",
    top_k_sections=10,  # Vector search results
    num_hops=1,  # Graph traversal depth
    model="gpt-4"
)

# Context retrieval
retrieve_graph_context(
    query="...",
    top_k_sections=10,
    num_hops=1,
    similarity_threshold=0.7,  # Min edge score
    max_similar_tickets=5  # Per seed ticket
)
```

---

## Error Handling

### Missing API Key
```python
result = answer_general("test query")
if 'error' in result:
    print(f"Error: {result['error']}")
    # Output: "Error: missing_api_key"
```

### No Context Found
```python
result = answer_graph_rag("completely unrelated query")
if 'error' in result:
    print(f"Error: {result['error']}")
    # Output: "No relevant sections found"
```

### OpenAI API Error
```python
try:
    result = answer_graph_rag("test query")
except Exception as e:
    print(f"API call failed: {e}")
```

---

## Performance Considerations

### Token Usage
- General answers: ~300-600 tokens
- Graph RAG answers: ~1000-2000 tokens (due to context)
- Cost: ~$0.03-$0.06 per graph RAG query (GPT-4)

### Latency
- General: ~2-5 seconds (API call only)
- Graph RAG:
  - Vector search: ~100ms
  - Neo4j query: ~200-500ms
  - LLM generation: ~3-8 seconds
  - **Total: ~4-9 seconds**

### Optimization Tips
1. **Use GPT-3.5-turbo** for faster/cheaper answers
2. **Reduce top_k_sections** (5-7 instead of 10)
3. **Limit num_hops** to 1 for most queries
4. **Cache context** for repeated queries
5. **Batch queries** when possible

---

## Prompt Engineering Notes

### GENERAL_PROMPT
- Clear role definition: "technical support assistant"
- Explicit formatting guidelines
- Emphasis on clarity and structure
- No context dependency

### GRAPH_RAG_PROMPT
- **Strict citation requirements**: Forces LLM to reference tickets
- **Context-only answering**: Prevents hallucination
- **Structured sections**: Ensures consistent format
- **Reasoning emphasis**: Encourages explanation of connections
- **Community integration**: Uses cluster insights

### Context Formatting
- **Sections**: Numbered, with ticket ID and similarity score
- **Graph info**: Quantitative metrics (nodes, edges, hops)
- **Communities**: Themes and representative tickets
- **Clear boundaries**: Separates different context types

---

## Testing

### Test General Answer
```bash
python -c "
from backend.llm.answer import answer_general
result = answer_general('How to debug memory leaks?')
print(result['answer'])
"
```

### Test Graph RAG Answer
```bash
python -c "
from backend.llm.answer import answer_graph_rag
result = answer_graph_rag('authentication timeout issue')
print(result['answer'])
print(f\"\\nTickets: {result['provenance']['ticket_ids']}\")
"
```

### Test Context Retrieval
```bash
python -c "
from backend.llm.answer import retrieve_graph_context
ctx = retrieve_graph_context('login problem')
print(f\"Sections: {len(ctx['sections'])}\")
print(f\"Tickets: {len(ctx['provenance']['ticket_ids'])}\")
print(f\"Communities: {len(ctx['community_context'])}\")
"
```

---

## Next Steps

Phase 4 is complete! The system now has:
✅ Dual answer generation (general + graph RAG)
✅ Comprehensive graph context retrieval
✅ Citation and provenance tracking
✅ Community insights integration
✅ Graph analysis in answers (clusters, nodes, edges)
✅ Reasoning extraction from relationships

Ready for:
- **Phase 5**: FastAPI endpoints for the answer functions
- **Phase 6**: Frontend integration with dual answer display
- **Phase 7**: Answer comparison and evaluation

Phase 4 Complete! 🎯
