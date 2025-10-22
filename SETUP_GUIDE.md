# Graph RAG - Complete Setup Guide

Step-by-step guide to get your Graph RAG application running.

## Prerequisites

✅ **Python 3.10+** - Backend
✅ **Node.js 18+** - Frontend  
✅ **Neo4j 5.x** - Graph database with GDS plugin
✅ **OpenAI API Key** - For LLM responses

## Installation Steps

### 1. Install Neo4j with GDS Plugin

#### Option A: Neo4j Desktop (Recommended)
1. Download Neo4j Desktop: https://neo4j.com/download/
2. Create a new project
3. Create a new database (v5.x)
4. Install Graph Data Science plugin from plugins panel
5. Start the database
6. Default credentials: `neo4j` / `neo4j` (you'll be prompted to change)

#### Option B: Docker
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["graph-data-science"]' \
  neo4j:latest
```

Verify Neo4j is running:
```bash
curl http://localhost:7474
```

### 2. Setup Backend

```bash
cd graph-rag-app/backend

# Create virtual environment
python -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Frontend

```bash
cd graph-rag-app/frontend

# Install dependencies
npm install
```

### 4. Configure Environment Variables

Create `.env` file in **project root** (`graph-rag-app/.env`):

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Embedding Model (default is fine)
EMBED_MODEL=sentence-transformers/e5-base-v2

# FAISS Index Storage
FAISS_INDEX_PATH=./faiss_index

# Neo4j Configuration (update password!)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# Application Server
APP_HOST=127.0.0.1
APP_PORT=8000

# Data Paths (optional - for ingestion)
CSV_PATH=/path/to/jira_issues_clean.csv
JSONL_PATH=/path/to/jira_issues_rag.jsonl
```

**Important**: Replace `your_neo4j_password_here` with your actual Neo4j password!

Create frontend `.env` file (`frontend/.env`):

```bash
cd frontend
cp .env.example .env
```

Edit `frontend/.env`:
```env
VITE_API_URL=http://127.0.0.1:8000
```

## Running the Application

### Terminal 1: Start Backend

```bash
cd graph-rag-app/backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

✅ Backend running at: **http://127.0.0.1:8000**
- API Docs (Swagger): http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

### Terminal 2: Start Frontend

```bash
cd graph-rag-app/frontend
npm run dev
```

✅ Frontend running at: **http://localhost:5173**

## First-Time Setup: Load Data

### Option 1: Using Swagger UI (Easiest)

1. Open http://127.0.0.1:8000/docs
2. Scroll to **POST /ingest**
3. Click "Try it out"
4. Click "Execute"
5. Wait for completion (5-30 minutes depending on data size)

### Option 2: Using cURL

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "similarity_threshold": 0.7,
    "similarity_top_k": 10,
    "community_algorithm": "louvain"
  }'
```

### Option 3: Using Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/ingest",
    json={
        "similarity_threshold": 0.7,
        "similarity_top_k": 10,
        "community_algorithm": "louvain"
    }
)

print(response.json())
```

This will:
1. Load data from CSV and JSONL files
2. Generate E5 embeddings
3. Build FAISS vector index
4. Create Neo4j graph
5. Run community detection
6. Store everything

**Expected output**:
```json
{
  "status": "success",
  "statistics": {
    "total_tickets": 1500,
    "total_sections": 7500,
    "similarity_edges": 12000,
    "communities": 25
  }
}
```

## Testing the Application

### Test 1: Health Check

```bash
curl http://127.0.0.1:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": {
      "status": "connected",
      "nodes": 9000
    },
    "vector_store": {
      "status": "loaded",
      "vectors": 7500
    }
  }
}
```

### Test 2: Ask a Question

Open the frontend at http://localhost:5173 and try:

**Example queries**:
- "How to fix authentication timeout issues?"
- "Memory leak debugging strategies"
- "Database connection pool configuration"

You should see:
1. General answer (purple card) - from GPT without context
2. Graph RAG answer (blue card) - with ticket citations
3. Interactive graph visualization below

### Test 3: API Query

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to fix authentication issues?",
    "model": "gpt-4",
    "top_k_sections": 10
  }'
```

## Verification Checklist

- [ ] Neo4j is running (http://localhost:7474 accessible)
- [ ] Backend health check returns "healthy"
- [ ] Backend shows `vector_store: "loaded"`
- [ ] Backend shows `neo4j: "connected"`
- [ ] Frontend loads without console errors
- [ ] Can submit a query in the UI
- [ ] General answer appears (purple card)
- [ ] Graph RAG answer appears (blue card)
- [ ] Graph visualization renders
- [ ] Can click clusters in legend
- [ ] Graph responds to interactions

## Troubleshooting

### Problem: Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
# Make sure virtual environment is activated
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: Neo4j connection failed

**Error**: `Failed to establish connection with Neo4j`

**Solution**:
1. Check Neo4j is running: `curl http://localhost:7474`
2. Verify credentials in `.env`
3. Try connecting with Neo4j Browser at http://localhost:7474
4. Update `NEO4J_PASSWORD` in `.env`

---

### Problem: OpenAI API error

**Error**: `Incorrect API key provided`

**Solution**:
1. Get API key from https://platform.openai.com/api-keys
2. Update `OPENAI_API_KEY` in `.env`
3. Ensure format is: `sk-proj-...` or `sk-...`

---

### Problem: FAISS index not found

**Error**: `No existing vector store found`

**Solution**:
Run ingestion first:
```bash
curl -X POST http://127.0.0.1:8000/ingest
```

---

### Problem: Frontend can't connect to backend

**Error**: `Network Error` or CORS error in browser console

**Solution**:
1. Verify backend is running: `curl http://127.0.0.1:8000/health`
2. Check `VITE_API_URL` in `frontend/.env`
3. Restart frontend dev server

---

### Problem: Graph not rendering

**Solution**:
1. Open browser DevTools (F12)
2. Check Console for errors
3. Verify `/graph/subgraph` endpoint returns data
4. Ensure Cytoscape.js loaded (check Network tab)

---

### Problem: Slow query responses

**Expected behavior**: 4-9 seconds for GPT-4

**To speed up**:
1. Use GPT-3.5-turbo instead: `"model": "gpt-3.5-turbo"`
2. Reduce `top_k_sections`: `"top_k_sections": 5`
3. Limit `num_hops`: `"num_hops": 1`

---

## Development Tips

### Restart Everything

```bash
# Kill all processes
# Terminal 1: Ctrl+C (backend)
# Terminal 2: Ctrl+C (frontend)

# Restart
cd backend && source .venv/bin/activate && uvicorn app:app --reload
cd frontend && npm run dev
```

### Clear FAISS Index

```bash
rm -rf faiss_index/
# Then re-run ingestion
```

### Clear Neo4j Database

In Neo4j Browser (http://localhost:7474):
```cypher
MATCH (n) DETACH DELETE n
```

Then re-run ingestion.

### View Logs

Backend logs appear in the terminal where `uvicorn` is running.

Frontend logs in browser DevTools Console.

---

## Next Steps

Once everything is running:

1. **Load your data**: Run ingestion with your CSV/JSONL files
2. **Ask questions**: Try the example queries
3. **Explore the graph**: Click clusters, zoom, pan
4. **Customize prompts**: Edit `backend/llm/prompts.py`
5. **Adjust styling**: Edit Tailwind classes in frontend components
6. **Add more data sources**: Create new ingestors

---

## Production Deployment

See `README.md` for Docker and production deployment instructions.

---

## Need Help?

- Backend docs: `backend/README.md`
- Frontend docs: `frontend/README.md`
- API docs: http://127.0.0.1:8000/docs
- Phase completion docs: `PHASE*_COMPLETE.md` files

---

✨ **You're all set!** Open http://localhost:5173 and start asking questions!

