# Graph RAG Application

Complete Graph RAG system combining Neo4j knowledge graphs, FAISS vector search, E5 embeddings, and GPT-4 for enhanced question answering with provenance.

## 🎯 Overview

This system provides **dual answers** to technical support questions:
1. **General Answer**: Context-free GPT-4 response
2. **Graph RAG Answer**: Graph-augmented response with citations to specific tickets, community insights, and provenance

### Key Features

- ✅ **Neo4j Knowledge Graph** with community detection (Louvain/Leiden)
- ✅ **FAISS Vector Search** with E5 embeddings
- ✅ **Dual Answer System** for comparison
- ✅ **Interactive Visualization** with Cytoscape.js
- ✅ **Ticket Citations** and provenance tracking
- ✅ **Beautiful Modern UI** with Tailwind CSS

---

## 🚀 Quick Start Guide

Follow these steps **exactly** to get the system running.

### Prerequisites

Install these first:
- ✅ **Python 3.10+** - [Download](https://www.python.org/downloads/)
- ✅ **Node.js 18+** - [Download](https://nodejs.org/)
- ✅ **Neo4j 5.x** - See Neo4j setup below
- ✅ **OpenAI API Key** - [Get key](https://platform.openai.com/api-keys)

---

## Step 1: Setup Python Virtual Environment

### macOS/Linux

```bash
# Navigate to project directory
cd graph-rag-app

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# You should see (.venv) in your terminal prompt
```

### Windows (Command Prompt)

```cmd
cd graph-rag-app
python -m venv .venv
.venv\Scripts\activate.bat
```

### Windows (PowerShell)

```powershell
cd graph-rag-app
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Note**: If you get an execution policy error on Windows PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Step 2: Install Python Dependencies

With the virtual environment activated:

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

This installs:
- FastAPI, Uvicorn
- Neo4j driver
- sentence-transformers (E5 embeddings)
- FAISS (vector search)
- OpenAI client
- Pydantic, orjson, and more

**Expected time**: 2-5 minutes

---

## Step 3: Setup Neo4j Database

### Option A: Neo4j Desktop (Recommended for Development)

1. **Download Neo4j Desktop**: https://neo4j.com/download/
2. **Install and open** Neo4j Desktop
3. **Create a new project** (e.g., "Graph RAG")
4. **Add a database**:
   - Click "Add" → "Local DBMS"
   - Name: `graph-rag`
   - Password: Choose a password (e.g., `password123`)
   - Version: 5.22.0 or higher
5. **Install Graph Data Science plugin**:
   - Click the database
   - Go to "Plugins" tab
   - Click "Install" on "Graph Data Science"
6. **Start the database**:
   - Click the "Start" button
   - Wait for status to show "Active"

**Connection details**:
- URI: `bolt://localhost:7687`
- Username: `neo4j`
- Password: `<your chosen password>`

### Option B: Docker (Recommended for Production)

```bash
docker run -d \
  --name graph-rag-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -e NEO4J_PLUGINS='["graph-data-science"]' \
  -v $HOME/neo4j/data:/data \
  neo4j:5.22.0
```

**Windows PowerShell**:
```powershell
docker run -d `
  --name graph-rag-neo4j `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/your_password `
  -e NEO4J_PLUGINS='["graph-data-science"]' `
  -v ${HOME}/neo4j/data:/data `
  neo4j:5.22.0
```

**Verify Neo4j is running**:
```bash
# Check HTTP interface
curl http://localhost:7474

# Or open in browser
open http://localhost:7474
```

---

## Step 4: Configure Environment Variables

### Create .env file

```bash
# Copy example file
cp .env.example .env
```

### Edit .env file

Open `.env` in your text editor and fill in these values:

```bash
# REQUIRED: OpenAI API Key
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Neo4j Configuration
# Update password to match your Neo4j setup
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Embedding Model (leave as default)
EMBED_MODEL=sentence-transformers/e5-base-v2

# FAISS Index Storage
FAISS_INDEX_PATH=./faiss_index

# Application Server
APP_HOST=127.0.0.1
APP_PORT=8000

# Data Paths (update to your actual file paths)
CSV_PATH=/mnt/data/jira_issues_clean.csv
JSONL_PATH=/mnt/data/jira_issues_rag.jsonl
```

**Important**: 
- Replace `your_password` with your actual Neo4j password
- Replace `sk-proj-xxx...` with your actual OpenAI API key
- Update data paths to point to your CSV/JSONL files

---

## Step 5: Run Backend Server

### Start the backend (keep this terminal open):

```bash
# Make sure virtual environment is activated
# You should see (.venv) in your prompt

# Run backend with auto-reload
uvicorn backend.app_main:app --host 127.0.0.1 --port 8001 --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify backend is running**:
- Open http://127.0.0.1:8000 in your browser
- Should see: `{"name": "Graph RAG API", ...}`
- **API Docs (Swagger)**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

---

## Step 6: Run Data Ingestion

**Important**: This loads your data into the system. Do this **once** before using the UI.

### Option A: Using cURL (Any OS)

Open a **new terminal** (keep backend running in the first terminal):

```bash
curl -X POST http://127.0.0.1:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "similarity_threshold": 0.7,
    "similarity_top_k": 10,
    "community_algorithm": "louvain"
  }'
```

### Option B: Using Python

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

### Option C: Using Swagger UI (Easiest)

1. Open http://127.0.0.1:8000/docs
2. Scroll to **POST /ingest**
3. Click **"Try it out"**
4. Click **"Execute"**
5. Wait for completion

### What Happens During Ingestion

1. ✅ Sets up Neo4j constraints and indexes
2. ✅ Loads data from CSV file
3. ✅ Loads data from JSONL file
4. ✅ Generates E5 embeddings for all sections
5. ✅ Builds FAISS vector index
6. ✅ Creates similarity edges between tickets
7. ✅ Runs community detection (Louvain/Leiden)
8. ✅ Stores community IDs in Neo4j

**Expected time**: 5-30 minutes (depending on data size)

**Expected output**:
```json
{
  "status": "success",
  "statistics": {
    "csv_tickets": 500,
    "csv_sections": 2500,
    "jsonl_tickets": 1000,
    "jsonl_sections": 5000,
    "total_tickets": 1500,
    "total_sections": 7500,
    "similarity_edges": 12000,
    "communities": 25,
    "total_errors": 0
  },
  "message": "Data ingestion and graph processing complete."
}
```

**If you see errors**: Check the troubleshooting section below.

---

## Step 7: Setup Frontend

Open a **new terminal** (keep backend running):

### Install Frontend Dependencies

```bash
cd frontend

# Install Node packages
npm install
```

**Expected time**: 1-2 minutes

### Configure Frontend Environment

```bash
# Copy example file
cp .env.example .env
```

Edit `frontend/.env`:
```bash
VITE_API_URL=http://127.0.0.1:8000
```

---

## Step 8: Run Frontend

In the frontend terminal:

```bash
npm run dev
```

**Expected output**:
```
  VITE v5.0.8  ready in 542 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Open the UI**: http://localhost:5173

---

## Step 9: Test the Application

### Test 1: Check Health

Open http://127.0.0.1:8000/health

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

### Test 2: Ask a Question in the UI

1. Open http://localhost:5173
2. Enter a question in the search bar:
   - "How to fix authentication timeout issues?"
   - "Memory leak debugging strategies"
   - "Database connection pool configuration"
3. Click **Search** or press **Enter**
4. Wait 4-9 seconds for results

**You should see**:
- ✅ Purple card (General Answer) on the left
- ✅ Blue card (Graph RAG Answer) on the right with:
  - Community badges at top
  - Ticket citations highlighted inline (e.g., `PROJ-123`)
  - Provenance info at bottom
- ✅ Interactive graph visualization below
- ✅ Cluster legend on the right

### Test 3: Explore the Graph

- **Click a cluster** in the legend → highlights that community
- **Hover over nodes** → shows tooltip with details
- **Click a node** → highlights its neighbors
- **Use zoom controls** → zoom in/out/fit
- **Click layout button** → cycles through layouts

---

## 🎉 Success!

If all tests pass, your Graph RAG system is fully operational!

---

## 🐛 Troubleshooting

### Problem 1: Import Errors or Module Not Found

**Symptoms**:
```
ModuleNotFoundError: No module named 'fastapi'
ImportError: cannot import name 'X' from 'Y'
```

**Solutions**:

1. **Ensure virtual environment is activated**:
   ```bash
   # You should see (.venv) in your prompt
   # If not, activate it:
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate      # Windows
   ```

2. **Reinstall with pinned versions**:
   ```bash
   pip uninstall -y -r backend/requirements.txt
   pip install --no-cache-dir -r backend/requirements.txt
   ```

3. **Clear and recreate virtual environment**:
   ```bash
   deactivate
   rm -rf .venv
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip wheel setuptools
   pip install -r backend/requirements.txt
   ```

4. **Check Python version**:
   ```bash
   python --version  # Should be 3.10+
   ```

5. **Install build tools** (if on Linux):
   ```bash
   sudo apt-get install python3-dev build-essential
   ```

---

### Problem 2: Neo4j Auth or Bolt Connection Errors

**Symptoms**:
```
ServiceUnavailable: Failed to establish connection
AuthError: The client is unauthorized due to authentication failure
Connection refused on port 7687
```

**Solutions**:

1. **Verify Neo4j is running**:
   ```bash
   curl http://localhost:7474
   # Should return HTML or JSON
   ```

2. **Check Neo4j Browser**:
   - Open http://localhost:7474
   - Try logging in with your credentials
   - If login fails, reset password in Neo4j Desktop

3. **Verify credentials in .env**:
   ```bash
   cat .env | grep NEO4J
   # Check that password matches Neo4j
   ```

4. **Test connection with Neo4j Browser**:
   - URI: `neo4j://localhost:7687`
   - Username: `neo4j`
   - Password: `<your password>`

5. **Check port 7687 is open**:
   ```bash
   # macOS/Linux
   lsof -i :7687
   
   # Windows PowerShell
   netstat -an | findstr 7687
   ```

6. **Restart Neo4j**:
   ```bash
   # Docker
   docker restart graph-rag-neo4j
   
   # Desktop
   # Stop and start database in Neo4j Desktop
   ```

7. **Check Neo4j logs**:
   ```bash
   # Docker
   docker logs graph-rag-neo4j
   
   # Desktop
   # Click database → "Open Folder" → logs/
   ```

---

### Problem 3: Embeddings Download Fails

**Symptoms**:
```
OSError: Can't load tokenizer for 'sentence-transformers/e5-base-v2'
HTTPError: 403 Client Error: Forbidden
Connection timeout downloading model
```

**Solutions**:

1. **Pre-download the model**:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('sentence-transformers/e5-base-v2')
   # This downloads to ~/.cache/huggingface/
   ```

2. **Set Hugging Face cache directory**:
   ```bash
   # Add to .env
   echo "HF_HOME=/path/to/cache" >> .env
   echo "TRANSFORMERS_CACHE=/path/to/cache" >> .env
   ```

3. **Download manually and use local path**:
   ```bash
   git clone https://huggingface.co/sentence-transformers/e5-base-v2
   
   # Update .env
   EMBED_MODEL=./e5-base-v2
   ```

4. **Check internet connection**:
   ```bash
   curl https://huggingface.co
   ```

5. **Use Hugging Face token** (if needed):
   ```bash
   # Add to .env
   HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
   ```

6. **Increase timeout**:
   ```python
   # In backend/retrieval/embedder.py
   import os
   os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/path/to/cache'
   ```

---

### Problem 4: Graph Empty After Ingestion

**Symptoms**:
```
{
  "status": "healthy",
  "services": {
    "neo4j": {"status": "connected", "nodes": 0},
    "vector_store": {"status": "empty", "vectors": 0}
  }
}
```

**Solutions**:

1. **Check ingestion logs**:
   - Look in the terminal where backend is running
   - Check for error messages during `/ingest`

2. **Verify data file paths**:
   ```bash
   cat .env | grep PATH
   # Check that CSV_PATH and JSONL_PATH exist
   
   ls -lh /mnt/data/jira_issues_clean.csv
   ls -lh /mnt/data/jira_issues_rag.jsonl
   ```

3. **Run ingestion with verbose output**:
   - Check the Swagger UI: http://127.0.0.1:8000/docs
   - Look at the response body for errors

4. **Check FAISS index was created**:
   ```bash
   ls -la faiss_index/
   # Should see: faiss.index and metadata.pkl
   ```

5. **Verify Neo4j has data**:
   - Open Neo4j Browser: http://localhost:7474
   - Run query:
     ```cypher
     MATCH (n) RETURN count(n) AS node_count
     ```
   - Should return > 0

6. **Check Neo4j constraints**:
   ```cypher
   SHOW CONSTRAINTS
   ```
   Should see constraints on `Ticket(id)` and `Section(id)`

7. **Re-run ingestion**:
   ```bash
   # Clear existing data first
   # In Neo4j Browser:
   # MATCH (n) DETACH DELETE n
   
   # Delete FAISS index
   rm -rf faiss_index/
   
   # Re-run ingestion
   curl -X POST http://127.0.0.1:8000/ingest
   ```

---

### Problem 5: Frontend Can't Connect to Backend

**Symptoms**:
```
Network Error
Failed to fetch
CORS error
```

**Solutions**:

1. **Verify backend is running**:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. **Check VITE_API_URL**:
   ```bash
   cat frontend/.env
   # Should be: VITE_API_URL=http://127.0.0.1:8000
   ```

3. **Restart frontend dev server**:
   ```bash
   # Ctrl+C to stop
   npm run dev
   ```

4. **Check browser console** (F12):
   - Look for CORS errors
   - Check network tab for failed requests

5. **Verify CORS configuration** in `backend/app.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],
       ...
   )
   ```

---

### Problem 6: Slow Query Responses

**Symptoms**:
- Queries take > 15 seconds
- Frontend times out

**Solutions**:

1. **Use GPT-3.5-turbo** instead of GPT-4:
   - In UI, this is automatic
   - For API: `"model": "gpt-3.5-turbo"`

2. **Reduce vector search top-k**:
   ```json
   {
     "query": "...",
     "top_k_sections": 5  // Instead of 10
   }
   ```

3. **Limit graph hops**:
   ```json
   {
     "query": "...",
     "num_hops": 1  // Instead of 2
   }
   ```

4. **Check Neo4j indexes**:
   ```cypher
   SHOW INDEXES
   ```
   Should see indexes on ticket and section properties

5. **Optimize FAISS index** (for large datasets):
   ```python
   # Use IVF index instead of Flat
   # In backend/retrieval/vector_store.py
   index = faiss.IndexIVFFlat(...)
   ```

---

### Problem 7: OpenAI API Errors

**Symptoms**:
```
AuthenticationError: Incorrect API key
RateLimitError: Rate limit exceeded
```

**Solutions**:

1. **Verify API key**:
   ```bash
   cat .env | grep OPENAI_API_KEY
   # Should start with sk-proj- or sk-
   ```

2. **Test API key**:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. **Check API quota**:
   - Visit https://platform.openai.com/usage

4. **Use different model**:
   ```json
   {
     "query": "...",
     "model": "gpt-3.5-turbo"  // Cheaper/faster
   }
   ```

---

### Problem 8: Port Already in Use

**Symptoms**:
```
Address already in use: 8000
EADDRINUSE: address already in use :::5173
```

**Solutions**:

1. **Find and kill process**:
   ```bash
   # macOS/Linux - Backend (port 8000)
   lsof -ti :8000 | xargs kill -9
   
   # macOS/Linux - Frontend (port 5173)
   lsof -ti :5173 | xargs kill -9
   
   # Windows PowerShell
   Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
   ```

2. **Use different port**:
   ```bash
   # Backend
   uvicorn backend.app:app --port 8001
   
   # Frontend
   npm run dev -- --port 5174
   ```

---

## 📊 System Requirements

### Minimum
- CPU: 2 cores
- RAM: 8 GB
- Disk: 10 GB free
- Network: Internet for model downloads

### Recommended
- CPU: 4+ cores
- RAM: 16 GB
- Disk: 20 GB free (for embeddings cache)
- GPU: Optional, for faster embeddings

---

## 📚 Additional Resources

- **Backend API Docs**: http://127.0.0.1:8000/docs
- **Backend README**: `backend/README.md`
- **Frontend README**: `frontend/README.md`
- **Setup Guide**: `SETUP_GUIDE.md`
- **Phase Completion Docs**: `PHASE*_COMPLETE.md`

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   FastAPI    │─────▶│    Neo4j    │
│ React + TS  │      │   Backend    │      │    Graph    │
│  Cytoscape  │◀─────│  + FAISS     │◀─────│     GDS     │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Embeddings  │
                     │  E5 + FAISS  │
                     └──────────────┘
```

---

## 🎉 You're All Set!

If you've completed all steps successfully, you now have a fully functional Graph RAG system with:

✅ Neo4j knowledge graph with community detection  
✅ FAISS vector search with E5 embeddings  
✅ FastAPI backend with dual answer generation  
✅ Beautiful React frontend with graph visualization  
✅ Complete provenance and citation tracking  

**Open http://localhost:5173 and start exploring!** 🚀

---

## 📝 License

MIT

## 🙏 Acknowledgments

- Neo4j Graph Database
- Facebook AI FAISS
- Hugging Face sentence-transformers
- OpenAI GPT-4
- Cytoscape.js
