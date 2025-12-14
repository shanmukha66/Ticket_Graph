# 🚀 Graph RAG Application

> **A Production-Ready Graph-Based Retrieval Augmented Generation System**

A complete, enterprise-grade **Graph RAG (Retrieval Augmented Generation)** system that combines Neo4j knowledge graphs, FAISS vector search, E5 embeddings, and GPT-4 for enhanced question answering with full provenance tracking and community insights.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![Neo4j 5.x](https://img.shields.io/badge/neo4j-5.x-008CC1.svg)](https://neo4j.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Demo Video](#-demo-video)
- [Key Features](#-key-features)
- [System Architecture](#️-system-architecture)
- [Data Ingestion Flow](#-data-ingestion-flow)
- [Retrieval & Query Flow](#-retrieval--query-flow)
- [Quick Start](#-quick-start)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Running the Application](#-running-the-application)
- [Usage Examples](#-usage-examples)
- [API Documentation](#-api-documentation)
- [Clustering Demo](#-clustering-demo)
- [Frontend Features](#-frontend-features)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Performance](#-performance)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

This system provides **dual answers** to technical support questions, allowing users to compare context-free AI responses with graph-augmented answers backed by real ticket data:

1. **General Answer**: Context-free GPT-4 response (baseline comparison)
2. **Graph RAG Answer**: Graph-augmented response with:
   - ✅ **Inline ticket citations** (e.g., `PROJ-123`)
   - ✅ **Community insights** from graph clustering
   - ✅ **Complete provenance** (tickets, sections, communities)
   - ✅ **Interactive visualization** of the knowledge graph

### What Makes This Special?

- **Dual Answer Comparison**: See the difference between generic AI and context-aware responses
- **Full Provenance**: Every answer includes citations to source tickets and sections
- **Community Detection**: Automatic clustering using Louvain/Leiden algorithms
- **Clustering Analytics**: Compare K-Means, Agglomerative, and DBSCAN algorithms
- **Production Ready**: Complete with error handling, health checks, and monitoring
- **Interactive Visualization**: Explore the knowledge graph with Cytoscape.js

## 🎥 Demo Video

<div align="center">
  
[![Watch the Demo](https://img.youtube.com/vi/ZpYMzyuGABs/maxresdefault.jpg)](https://youtu.be/ZpYMzyuGABs)

**Click to watch: Graph RAG Application - Complete Walkthrough**

</div>

---

## ✨ Key Features

### Backend Capabilities

| Feature | Description |
|---------|-------------|
| 🗄️ **Neo4j Knowledge Graph** | Stores tickets, sections, and similarity relationships |
| 🧠 **Community Detection** | Louvain/Leiden algorithms for automatic clustering |
| 🔍 **FAISS Vector Search** | Fast similarity search using E5 embeddings |
| 🤖 **Dual Answer System** | General + Graph RAG answers for comparison |
| 📝 **Ticket Citations** | Inline citations with provenance tracking |
| 🎯 **Smart Context Retrieval** | Vector search + graph traversal (1-N hops) |
| 🧪 **Clustering Demo** | Compare K-Means, Agglomerative, and DBSCAN algorithms |
| 🔍 **Ticket Search** | Cluster-aware search with smart routing |
| 📊 **Benchmarking** | Performance metrics and quality scoring |
| ⚡ **FastAPI Backend** | Modern async Python with automatic OpenAPI docs |
| 🔒 **Health Monitoring** | Real-time status checks for all services |

### Frontend Features

| Feature | Description |
|---------|-------------|
| 🎨 **Beautiful Modern UI** | Tailwind CSS with glass morphism and gradients |
| 📊 **Interactive Graph** | Cytoscape.js visualization with zoom/pan/filter |
| 🏷️ **Smart Citations** | Automatic highlighting of ticket IDs in answers |
| 🎯 **Cluster Filtering** | Click clusters to focus on specific communities |
| 🌈 **Community Colors** | 10-color palette for visual clustering |
| 🧪 **Clustering Analytics** | Compare clustering algorithms with performance metrics |
| 🔍 **Cluster Search** | Search tickets across different cluster types |
| ⚡ **Parallel Requests** | Simultaneous API calls for faster responses |
| 📱 **Responsive Design** | Works beautifully on desktop and tablet |
| 🔄 **Real-time Updates** | Live loading states and smooth transitions |

---

## 🏗️ System Architecture

The application follows a modern three-tier architecture:

![System Architecture](architecture.png)

### Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["🌐 Frontend Layer - React + TypeScript + Tailwind CSS"]
        direction TB
        UI[User Interface<br/>localhost:5173]
        QueryBox[QueryBox<br/>Search Input]
        AnswerCard[AnswerCard<br/>Dual Answers]
        GraphPanel[GraphPanel<br/>Cytoscape.js]
        ClusteringDemo[ClusteringDemo<br/>Analytics]
    end
    
    subgraph Backend["⚙️ Backend Layer - FastAPI + Python 3.10+"]
        direction TB
        API[FastAPI Server<br/>127.0.0.1:8001]
        Ingest[POST /ingest<br/>Data Ingestion]
        Ask[POST /ask<br/>Dual Answers]
        Graph[GET /graph/subgraph<br/>Graph Visualization]
        Search[POST /search/tickets<br/>Cluster Search]
        Cluster[POST /clustering-demo/cluster<br/>Clustering Analysis]
        Health[GET /health<br/>Health Check]
    end
    
    subgraph Services["🔧 Services Layer"]
        direction LR
        Embedding[Embedding Service<br/>E5-base-v2<br/>768-dim vectors]
        VectorStore[FAISS Vector Store<br/>IndexFlatIP<br/>Similarity Search]
        Neo4j[Neo4j Graph DB<br/>5.22.0+<br/>GDS Plugin]
        LLM[OpenAI GPT-4<br/>Answer Generation]
    end
    
    UI --> QueryBox
    UI --> AnswerCard
    UI --> GraphPanel
    UI --> ClusteringDemo
    
    QueryBox -.->|HTTP/REST<br/>Axios| API
    AnswerCard -.->|HTTP/REST<br/>Axios| API
    GraphPanel -.->|HTTP/REST<br/>Axios| API
    ClusteringDemo -.->|HTTP/REST<br/>Axios| API
    
    API --> Ingest
    API --> Ask
    API --> Graph
    API --> Search
    API --> Cluster
    API --> Health
    
    Ingest --> Embedding
    Ingest --> VectorStore
    Ingest --> Neo4j
    
    Ask --> Embedding
    Ask --> VectorStore
    Ask --> Neo4j
    Ask --> LLM
    
    Graph --> VectorStore
    Graph --> Neo4j
    
    Search --> Embedding
    Search --> Neo4j
    
    Cluster --> Embedding
    Cluster --> Neo4j
    
    style Frontend fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style Backend fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000
    style Services fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#000
    style UI fill:#bbdefb,stroke:#1976d2,stroke-width:2px
    style API fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style Neo4j fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style VectorStore fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style Embedding fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style LLM fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
```

### Technology Stack

**Backend:**
- **FastAPI** (0.115.6) - Modern Python web framework
- **Neo4j** (5.27.0) - Graph database with GDS plugin
- **FAISS** (1.12.0) - Vector similarity search (CPU)
- **sentence-transformers** (3.3.1) - E5 embedding model
- **OpenAI** (1.57.4) - GPT-4 for answer generation
- **Pydantic** (2.10.6) - Data validation
- **scikit-learn** (1.6.1) - Clustering algorithms
- **uvicorn** - ASGI server
- **orjson** (3.10.15) - Fast JSON serialization

**Frontend:**
- **React** (18.2) - UI framework
- **TypeScript** - Type safety
- **Vite** (5.0) - Build tool with HMR
- **Tailwind CSS** (3.3) - Utility-first styling
- **Cytoscape.js** (3.28) - Graph visualization
- **Axios** (1.6) - HTTP client
- **Lucide React** - Icon library
- **Framer Motion** - Animations

**Database:**
- **Neo4j** (5.22.0+) with Graph Data Science plugin
- **FAISS** index files (persistent vector store)

---

## 📥 Data Ingestion Flow

The system ingests ticket data from CSV/JSONL files and builds a comprehensive knowledge graph:

![Data Ingestion Flow](Data%20injestion%20sequence%20Diagram.png)

### Ingestion Pipeline Stages

```mermaid
flowchart TD
    Start([📄 CSV + JSONL Files<br/>Raw Ticket Data<br/>Tickets & Sections]) --> Parse[1️⃣ Parse & Validate<br/>📋 Load tickets and sections<br/>✓ Validate required fields<br/>🔧 Structure data for graph]
    
    Parse --> Embed[2️⃣ Generate Embeddings<br/>🤖 E5-base-v2 model<br/>📊 768-dimensional vectors<br/>📝 Process all section text]
    
    Embed --> FAISS[3️⃣ Build FAISS Index<br/>🔍 IndexFlatIP Inner Product<br/>💾 Store vectors + metadata<br/>⚡ Enable fast similarity search]
    
    FAISS --> Neo4jNodes[4️⃣ Create Neo4j Graph<br/>🎫 Ticket nodes with properties<br/>📑 Section nodes linked to tickets<br/>🔗 HAS_SECTION relationships]
    
    Neo4jNodes --> Similarity[5️⃣ Connect Similar Tickets<br/>📐 Compute cosine similarity<br/>🔗 Create SIMILAR_TO edges<br/>🎯 Filter by threshold 0.7<br/>🔝 Limit top-k per ticket 10]
    
    Similarity --> Community[6️⃣ Run Community Detection<br/>🧠 GDS Louvain/Leiden algorithm<br/>🏷️ Assign community IDs<br/>💾 Store in ticket properties<br/>📊 Generate cluster summaries]
    
    Community --> End([✅ Knowledge Graph Ready<br/>🎫 Tickets with sections<br/>🕸️ Similarity network<br/>👥 Community clusters<br/>🔍 Searchable embeddings])
    
    style Start fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Parse fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style Embed fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style FAISS fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style Neo4jNodes fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style Similarity fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style Community fill:#e0f2f1,stroke:#00796b,stroke-width:2px
    style End fill:#c8e6c9,stroke:#388e3c,stroke-width:3px
```

### Graph Schema

![Graph Schema](Graph%20schema.png)

```mermaid
erDiagram
    TICKET ||--o{ SECTION : "HAS_SECTION"
    TICKET ||--o{ TICKET : "SIMILAR_TO"
    
    TICKET {
        string id PK "Unique identifier"
        string summary "Ticket summary"
        string status "Status: Open/Closed/Resolved"
        string priority "Priority level"
        string project "Project code"
        string created "Creation timestamp"
        string updated "Last update timestamp"
        int communityId "Community cluster ID"
        string text_for_rag "Full text content"
    }
    
    SECTION {
        string id PK "Section identifier"
        string ticket_id FK "Parent ticket ID"
        string key "Section type: summary/description/resolution"
        string text "Section content"
        float[] embedding_vector "768-dim E5 embedding"
    }
    
    SIMILAR_TO {
        float score "Similarity score 0.0-1.0"
    }
```

**Nodes:**
- `Ticket`: Contains ticket metadata (id, summary, status, priority, etc.)
- `Section`: Contains text chunks (summary, description, resolution, etc.)

**Relationships:**
- `HAS_SECTION`: Links tickets to their sections
- `SIMILAR_TO`: Connects similar tickets (weighted by score)

**Properties:**
- Tickets have `communityId` from clustering
- Sections have embeddings (stored in FAISS)
- Similarity edges have `score` (0.0-1.0)

---

## 🔍 Retrieval & Query Flow

When a user asks a question, the system performs a sophisticated multi-stage retrieval:

![Retrieval Sequence](Retreval%20sequence%20diagram.png)

### Query Processing Pipeline

```mermaid
flowchart TD
    Query([👤 User Query<br/>"How to fix authentication timeout?"]) --> Embed[1️⃣ Embed Query<br/>🤖 Convert to E5 embedding<br/>📊 768-dimensional vector<br/>🔄 Same model as documents]
    
    Embed --> VectorSearch[2️⃣ FAISS Vector Search<br/>🔍 Find top-k similar sections<br/>📈 Returns section IDs + scores<br/>🎯 Typical k = 10-20]
    
    VectorSearch --> GraphExpand[3️⃣ Graph Expansion Neo4j<br/>🎫 Get tickets owning top sections<br/>🕸️ Traverse SIMILAR_TO edges<br/>📏 1-2 hops traversal<br/>👥 Include community information]
    
    GraphExpand --> Context[4️⃣ Context Assembly<br/>📋 Organize sections by ticket<br/>🏷️ Add community cluster info<br/>📝 Format for LLM prompt]
    
    Context --> General[💜 General Answer<br/>🤖 GPT-4<br/>❌ No Context<br/>📄 Generic response]
    Context --> GraphRAG[💙 Graph RAG Answer<br/>🤖 GPT-4 + Full Context<br/>✅ With Citations<br/>📚 Evidence-based]
    Context --> Subgraph[📊 Subgraph for Viz<br/>🎨 Cytoscape.js Format<br/>🕸️ Interactive graph]
    
    General --> Response[📤 Return to User<br/>💜 General answer<br/>💙 Graph RAG answer<br/>📝 Ticket citations<br/>🔗 Full provenance<br/>📊 Graph visualization]
    GraphRAG --> Response
    Subgraph --> Response
    
    style Query fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Embed fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style VectorSearch fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style GraphExpand fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style Context fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style General fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style GraphRAG fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Subgraph fill:#e0f2f1,stroke:#00796b,stroke-width:2px
    style Response fill:#c8e6c9,stroke:#388e3c,stroke-width:3px
```

### Dual Answer System

**General Answer:**
- Pure GPT-4 response without context
- Baseline for comparison
- Shows generic AI knowledge

**Graph RAG Answer:**
- Context-enriched response
- Inline ticket citations (e.g., `PROJ-4523`)
- Community insights
- Full provenance tracking
- Evidence-based and verifiable

---

## ⚡ Quick Start

Get the system running in **under 30 minutes**:

```bash
# 1. Clone and setup backend
cd Ticket_Graph
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# 2. Start Neo4j (Docker method)
docker-compose up -d neo4j

# Or use Neo4j Desktop (see Installation section)

# 3. Configure environment
# Create .env file in project root (see Configuration section)

# 4. Start backend (Terminal 1)
cd backend
uvicorn app_main:app --host 127.0.0.1 --port 8001 --reload

# 5. Run ingestion (Terminal 2)
curl -X POST http://127.0.0.1:8001/ingest

# 6. Setup and run frontend (Terminal 3)
cd frontend
npm install
npm run dev

# 7. Open browser
# Frontend: http://localhost:5173
# API Docs: http://127.0.0.1:8001/docs
```

---

## 📋 Prerequisites

### Required Software

| Software | Version | Purpose | Download |
|----------|---------|---------|----------|
| **Python** | 3.10+ | Backend runtime | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | Frontend build | [nodejs.org](https://nodejs.org/) |
| **Neo4j** | 5.x | Graph database | [neo4j.com](https://neo4j.com/download/) |
| **OpenAI API Key** | - | LLM access | [platform.openai.com](https://platform.openai.com/api-keys) |
| **Docker** (optional) | - | Neo4j container | [docker.com](https://www.docker.com/) |

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 8 GB
- Disk: 10 GB free
- Network: Internet for model downloads

**Recommended:**
- CPU: 4+ cores
- RAM: 16 GB
- Disk: 20 GB free (for embeddings cache)
- GPU: Optional, for faster embeddings

---

## 📦 Installation

### Step 1: Setup Python Environment

```bash
# Navigate to project directory
cd /path/to/Ticket_Graph

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows Command Prompt:
.venv\Scripts\activate.bat

# Windows PowerShell:
.venv\Scripts\Activate.ps1
```

**Note for Windows PowerShell users:**
If you encounter an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 2: Install Backend Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r backend/requirements.txt
```

**Expected installation time:** 2-5 minutes

**Installed packages:**
- FastAPI, Uvicorn (web framework)
- Neo4j driver
- sentence-transformers (E5 embeddings)
- FAISS (vector search)
- OpenAI client
- Pydantic, orjson (utilities)
- scikit-learn, scipy (clustering)

### Step 3: Setup Neo4j Database

#### Option A: Neo4j Desktop (Recommended for Development)

1. **Download and install** Neo4j Desktop: https://neo4j.com/download/
2. **Open** Neo4j Desktop
3. **Create a new project** (e.g., "Graph RAG")
4. **Add a database:**
   - Click "Add" → "Local DBMS"
   - Name: `graph-rag`
   - Password: Choose a secure password
   - Version: 5.22.0 or higher
5. **Install Graph Data Science plugin:**
   - Click the database
   - Go to "Plugins" tab
   - Click "Install" on "Graph Data Science"
6. **Start the database:**
   - Click the "Start" button
   - Wait for status to show "Active"

**Connection details:**
- URI: `bolt://localhost:7687`
- Username: `neo4j`
- Password: `<your chosen password>`

#### Option B: Docker (Recommended for Production)

```bash
# macOS/Linux:
docker-compose up -d neo4j

# Or manually:
docker run -d \
  --name graph-rag-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -e NEO4J_PLUGINS='["graph-data-science"]' \
  -v $HOME/neo4j/data:/data \
  neo4j:5.22.0

# Windows PowerShell:
docker run -d `
  --name graph-rag-neo4j `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/your_password `
  -e NEO4J_PLUGINS='["graph-data-science"]' `
  -v ${HOME}/neo4j/data:/data `
  neo4j:5.22.0
```

**Verify Neo4j is running:**
```bash
curl http://localhost:7474
# Should return HTML

# Or open in browser:
open http://localhost:7474  # macOS
start http://localhost:7474 # Windows
```

### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
```

**Expected installation time:** 1-2 minutes

---

## ⚙️ Configuration

### Backend Environment Variables

Create a `.env` file in the **project root**:

```bash
# Copy example file if it exists
# cp .env.example .env
```

Edit `.env` with your values:

```bash
# ============================================
# OpenAI Configuration (REQUIRED)
# ============================================
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================
# Neo4j Configuration
# ============================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# ============================================
# Embedding Model
# ============================================
# Default model (recommended)
EMBED_MODEL=sentence-transformers/e5-base-v2

# ============================================
# Vector Store
# ============================================
FAISS_INDEX_PATH=./faiss_index

# ============================================
# Application Server
# ============================================
APP_HOST=127.0.0.1
APP_PORT=8001

# ============================================
# Data Paths (Update to your actual files)
# ============================================
CSV_PATH=/mnt/data/jira_issues_clean.csv
JSONL_PATH=/mnt/data/jira_issues_rag.jsonl
```

**Important:**
- Replace `sk-proj-xxx...` with your actual OpenAI API key
- Replace `your_password_here` with your Neo4j password
- Update `CSV_PATH` and `JSONL_PATH` to your data files

### Frontend Environment Variables

Create `frontend/.env`:

```bash
cd frontend
# cp .env.example .env  # if example exists
```

Edit `frontend/.env`:

```bash
VITE_API_URL=http://127.0.0.1:8001
```

---

## 🚀 Running the Application

### Terminal 1: Start Backend

```bash
# Activate virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Navigate to backend
cd backend

# Start backend with auto-reload
uvicorn app_main:app --host 127.0.0.1 --port 8001 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify backend:**
- API Root: http://127.0.0.1:8001
- Interactive Docs: http://127.0.0.1:8001/docs
- Health Check: http://127.0.0.1:8001/health

### Terminal 2: Run Data Ingestion (First Time Only)

**Important:** Run this once to load your data into the system.

#### Method 1: Using Swagger UI (Easiest)

1. Open http://127.0.0.1:8001/docs
2. Scroll to **POST /ingest**
3. Click **"Try it out"**
4. Click **"Execute"**
5. Wait for completion (5-30 minutes depending on data size)

#### Method 2: Using cURL

```bash
curl -X POST http://127.0.0.1:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "similarity_threshold": 0.7,
    "similarity_top_k": 10,
    "community_algorithm": "louvain"
  }'
```

#### Method 3: Using Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8001/ingest",
    json={
        "similarity_threshold": 0.7,
        "similarity_top_k": 10,
        "community_algorithm": "louvain"
    }
)

print(response.json())
```

**Expected output:**
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

### Terminal 3: Start Frontend

```bash
cd frontend
npm run dev
```

**Expected output:**
```
  VITE v5.0.8  ready in 542 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Open the application:**
- Frontend UI: http://localhost:5173
- Backend API: http://127.0.0.1:8001
- API Docs: http://127.0.0.1:8001/docs

---

## 💡 Usage Examples

### Test 1: Health Check

Verify all services are running:

```bash
curl http://127.0.0.1:8001/health
```

**Expected response:**
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

### Test 2: Ask a Question via UI

1. Open http://localhost:5173
2. Enter a question:
   - "How to fix authentication timeout issues?"
   - "Memory leak debugging strategies"
   - "Database connection pool configuration"
3. Click **Search** or press **Enter**
4. Wait 4-9 seconds for results

**You should see:**
- 💜 Purple card (General Answer) - Context-free GPT-4 response
- 💙 Blue card (Graph RAG Answer) with:
  - Community badges at top
  - Inline ticket citations (e.g., `PROJ-123`)
  - Provenance information at bottom
- 📊 Interactive graph visualization below
- 🎨 Cluster legend on the right side

### Test 3: Ask a Question via API

```bash
curl -X POST http://127.0.0.1:8001/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to fix authentication timeout issues?",
    "model": "gpt-4",
    "top_k_sections": 10,
    "num_hops": 1
  }'
```

### Test 4: Get Graph Subgraph

```bash
curl "http://127.0.0.1:8001/graph/subgraph?query=authentication&top_k=10&num_hops=1"
```

### Test 5: Explore the Graph Visualization

In the UI:
- **Click a cluster** in the legend → highlights that community
- **Hover over nodes** → shows tooltip with details
- **Click a node** → highlights its neighbors
- **Use zoom controls** → zoom in/out/fit to screen
- **Click layout button** → cycles through layouts (force/circle/grid)

### Test 6: Clustering Demo

1. Open http://localhost:5173
2. Click the **"Clustering Demo"** tab
3. Enter a query: "billing issue" or "authentication error"
4. Select:
   - **Subset Size**: A (100), B (500), C (1000), or All
   - **Algorithm**: K-Means, Agglomerative, DBSCAN, or All
5. Click **"Run Clustering"**
6. View the comparison table with all metrics:
   - Computation time
   - Query time
   - Total time
   - Silhouette score
   - Number of clusters
   - Average cluster size

**Expected results:**
- Summary cards showing fastest, best quality, and most clusters
- Comparison table with all 9 combinations
- Detailed cluster information for each combination

### Test 7: Cluster Search

1. Open http://localhost:5173
2. Click the **"Cluster Search"** tab
3. Enter a search query
4. View results across different cluster types (A, B, C)
5. Compare performance and quality metrics

---

## 📚 API Documentation

### Interactive Documentation

The backend provides interactive API documentation:
- **Swagger UI**: http://127.0.0.1:8001/docs
- **ReDoc**: http://127.0.0.1:8001/redoc

### Core Endpoints

#### `GET /`
**Root endpoint with API information**

```bash
curl http://127.0.0.1:8001/
```

#### `GET /health`
**Health check for all services**

Response includes Neo4j connection status and vector store status.

#### `POST /ingest`
**Run complete data ingestion pipeline**

Request body (all optional):
```json
{
  "csv_path": "/path/to/data.csv",
  "jsonl_path": "/path/to/data.jsonl",
  "similarity_threshold": 0.7,
  "similarity_top_k": 10,
  "community_algorithm": "louvain"
}
```

#### `POST /ask`
**Generate dual answers (general + graph RAG)**

Request body:
```json
{
  "query": "Your question here",
  "model": "gpt-4",
  "top_k_sections": 10,
  "num_hops": 1
}
```

Response includes:
- General answer (no context)
- Graph RAG answer (with context)
- Ticket citations
- Community insights
- Full provenance

#### `GET /graph/subgraph`
**Get Cytoscape-friendly subgraph for visualization**

Query parameters:
- `query` (required): Search query
- `top_k` (optional, default=10): Number of sections
- `num_hops` (optional, default=1): Graph traversal depth
- `include_communities` (optional, default=true)

#### `POST /search/tickets`
**Cluster-aware ticket search**

Request body:
```json
{
  "query": "login issue",
  "top_k": 10,
  "use_smart_routing": true,
  "apply_feedback_boost": true
}
```

#### `POST /clustering-demo/cluster`
**Run clustering analysis**

Request body:
```json
{
  "query": "login issue",
  "top_k": 1000,
  "subset_size": 100,
  "algorithm": "kmeans"
}
```

#### `GET /clustering-demo/stats`
**Get clustering statistics**

Returns total tickets, available subset sizes, and algorithms.

#### `POST /benchmark/query`
**Benchmark query across cluster types**

#### `GET /benchmark/stats`
**Get cluster statistics and quality metrics**

See [backend/API_README.md](backend/API_README.md) for complete API documentation.

---

## 🧪 Clustering Demo

The Clustering Demo feature allows you to compare different clustering algorithms (K-Means, Agglomerative Clustering, and DBSCAN) across different ticket subset sizes (100, 500, 1000 tickets) to analyze performance and cluster quality.

### Features

- **Multiple Subset Sizes**: Compare clustering on 100, 500, or 1000 tickets
- **Three Algorithms**: K-Means, Agglomerative Clustering, and DBSCAN
- **Performance Metrics**: Computation time, query time, and total execution time
- **Quality Metrics**: Silhouette score, number of clusters, average cluster size
- **Interactive Comparison**: Side-by-side comparison of all 9 combinations
- **Query-Based Clustering**: Run clustering on tickets relevant to your search query

### Accessing the Demo

1. **Via UI**: 
   - Open http://localhost:5173
   - Click on the **"Clustering Demo"** tab
   - Enter a search query (e.g., "login issue", "billing error")
   - Select subset size and algorithm (or choose "All" for all combinations)
   - Click **"Run Clustering"**

2. **Via API**:
   ```bash
   curl -X POST http://127.0.0.1:8001/clustering-demo/cluster \
     -H "Content-Type: application/json" \
     -d '{
       "query": "login issue",
       "top_k": 1000,
       "subset_size": 100,
       "algorithm": "kmeans"
     }'
   ```

### Clustering Algorithms

| Algorithm | Description | Use Case |
|-----------|-------------|----------|
| **K-Means** | Partition-based clustering with fixed number of clusters | Fast, good for balanced clusters |
| **Agglomerative** | Hierarchical clustering with cosine similarity | High quality, precise groupings |
| **DBSCAN** | Density-based clustering, handles noise | Finds natural clusters, handles outliers |

### Subset Sizes

- **A (100 tickets)**: Fast clustering, good for quick analysis
- **B (500 tickets)**: Balanced performance and quality
- **C (1000 tickets)**: Comprehensive analysis, best quality metrics

### Performance Comparison

The demo automatically runs all 9 combinations (3 subset sizes × 3 algorithms) and provides:
- **Fastest**: Combination with lowest total execution time
- **Best Quality**: Highest silhouette score
- **Most Clusters**: Maximum number of clusters found

For more details, see [CLUSTERING_DEMO_README.md](CLUSTERING_DEMO_README.md).

---

## 🎨 Frontend Features

### Components

| Component | Description |
|-----------|-------------|
| **QueryBox** | Large search input with example queries |
| **AnswerCard** | Side-by-side dual answer display |
| **GraphPanel** | Interactive Cytoscape.js visualization |
| **ClusterLegend** | Community list with filtering |
| **TicketDetailsPanel** | Detailed ticket information on click |
| **ClusteringDemo** | Clustering algorithm comparison interface |
| **ClusterComparison** | Pre-computed cluster comparison view |
| **SkeletonLoader** | Loading states for better UX |

### Design System

**Color Palette:**
- General Answer: Purple (#8b5cf6)
- Graph RAG Answer: Blue gradient (#3b82f6 → #4f46e5)
- Communities: 10-color rotating palette
- Background: Subtle gradient (gray → blue → indigo)

**Visual Elements:**
- Soft shadows with hover effects
- Rounded corners (rounded-xl, rounded-lg)
- Smooth transitions (150-200ms)
- Glass morphism on header
- Gradient accents

### Interactive Graph Features

**Node Types:**
- **Ticket nodes**: Large, colored by community, size by degree
- **Section nodes**: Small, gray, labeled by section key

**Edge Types:**
- **SIMILAR_TO**: Solid orange, width by similarity score
- **HAS_SECTION**: Dashed gray, thin

**Layouts:**
- **cose-bilkent**: Force-directed (default)
- **circle**: Circular layout
- **grid**: Grid layout

See [frontend/README.md](frontend/README.md) for component documentation.

---

## 📁 Project Structure

```
Ticket_Graph/
├── README.md                           # This file
├── SETUP_GUIDE.md                      # Detailed setup walkthrough
├── DEMO_GUIDE.md                        # Demo usage guide
├── CLUSTERING_DEMO_README.md            # Clustering demo guide
├── ARCHITECTURE.md                      # System architecture details
├── docker-compose.yml                  # Docker Compose configuration
├── .gitignore                          # Git ignore rules
│
├── backend/                            # Python backend
│   ├── README.md                       # Backend documentation
│   ├── API_README.md                   # API documentation
│   ├── requirements.txt                # Python dependencies
│   ├── app_main.py                     # FastAPI application entry
│   │
│   ├── app/                            # Application code
│   │   ├── main.py                     # FastAPI app instance
│   │   ├── api/                        # API endpoints
│   │   │   ├── embeddings.py
│   │   │   ├── graph.py
│   │   │   ├── search.py
│   │   │   ├── ticket_search.py
│   │   │   ├── benchmark.py
│   │   │   └── clustering_demo.py
│   │   ├── core/                       # Configuration
│   │   │   └── config.py
│   │   ├── models/                     # Pydantic schemas
│   │   │   └── schemas.py
│   │   └── services/                   # Business logic
│   │       ├── embedding_service.py
│   │       ├── faiss_service.py
│   │       └── neo4j_service.py
│   │
│   ├── graph/                          # Neo4j graph operations
│   │   ├── README.md
│   │   ├── build_graph.py              # Neo4jGraph class
│   │   ├── community.py                # Community detection
│   │   └── cypher/                     # Cypher queries
│   │       ├── constraints.cypher
│   │       ├── gds.cypher
│   │       └── queries.cypher
│   │
│   ├── ingestors/                      # Data ingestion
│   │   ├── load_csv.py                 # CSV loader
│   │   ├── load_jsonl.py              # JSONL loader
│   │   └── schema_template.yml        # Section definitions
│   │
│   ├── retrieval/                      # Vector search
│   │   ├── embedder.py                 # E5 embeddings
│   │   └── vector_store.py             # FAISS operations
│   │
│   ├── llm/                            # LLM integration
│   │   ├── answer.py                   # Answer generation
│   │   └── prompts.py                  # Prompt templates
│   │
│   └── utils/                          # Utilities
│       └── env.py                      # Environment management
│
├── frontend/                           # React frontend
│   ├── README.md                       # Frontend documentation
│   ├── package.json                    # Node dependencies
│   ├── vite.config.ts                  # Vite configuration
│   ├── tailwind.config.js              # Tailwind configuration
│   ├── tsconfig.json                   # TypeScript configuration
│   │
│   ├── public/                         # Static assets
│   │
│   └── src/                            # Source code
│       ├── main.tsx                    # Entry point
│       ├── App.tsx                     # Main component
│       ├── index.css                   # Global styles
│       │
│       ├── components/                 # React components
│       │   ├── QueryBox.tsx
│       │   ├── AnswerCard.tsx
│       │   ├── AnswerCardEnhanced.tsx
│       │   ├── GraphPanel.tsx
│       │   ├── GraphVisualization.tsx
│       │   ├── ClusterLegend.tsx
│       │   ├── ControlPanel.tsx
│       │   ├── SearchPanel.tsx
│       │   ├── TicketDetailsPanel.tsx
│       │   ├── Button.tsx
│       │   ├── SkeletonLoader.tsx
│       │   ├── ClusteringDemo.tsx
│       │   ├── ClusterComparison.tsx
│       │   └── ui/                     # UI primitives
│       │       ├── skeleton.tsx
│       │       └── toast.tsx
│       │
│       ├── lib/                        # Utilities
│       │   ├── api.ts                  # API client
│       │   └── utils.ts                # Helper functions
│       │
│       └── types/                      # TypeScript types
│           └── index.ts
│
├── Phases/                             # Documentation
│   ├── PHASE1_COMPLETE.md
│   ├── PHASE2_COMPLETE.md
│   ├── PHASE3_COMPLETE.md
│   ├── PHASE4_COMPLETE.md
│   ├── PHASE5_COMPLETE.md
│   ├── PHASE6_COMPLETE.md
│   ├── PHASE6_SUMMARY.md
│   ├── PHASE7_COMPLETE.md
│   ├── PHASE8_COMPLETE.md
│   └── PROJECT_COMPLETE.md
│
├── faiss_index.faiss                   # FAISS index (generated)
└── faiss_index.meta.pkl                # FAISS metadata (generated)
```

---

## 🐛 Troubleshooting

### Problem 1: Module Not Found Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
ImportError: cannot import name 'X' from 'Y'
```

**Solutions:**

1. **Ensure virtual environment is activated:**
   ```bash
   # You should see (.venv) in your prompt
   # If not:
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate      # Windows
   ```

2. **Reinstall dependencies:**
   ```bash
   pip uninstall -y -r backend/requirements.txt
   pip install --no-cache-dir -r backend/requirements.txt
   ```

3. **Verify Python version:**
   ```bash
   python --version  # Should be 3.10+
   ```

### Problem 2: Neo4j Connection Failed

**Symptoms:**
```
ServiceUnavailable: Failed to establish connection
AuthError: The client is unauthorized
Connection refused on port 7687
```

**Solutions:**

1. **Verify Neo4j is running:**
   ```bash
   curl http://localhost:7474
   ```

2. **Check credentials in .env:**
   ```bash
   cat .env | grep NEO4J
   ```

3. **Test connection in Neo4j Browser:**
   - Open http://localhost:7474
   - Try logging in with your credentials

4. **Restart Neo4j:**
   ```bash
   # Docker:
   docker restart graph-rag-neo4j
   
   # Desktop: Stop and start in Neo4j Desktop
   ```

### Problem 3: Embeddings Download Fails

**Symptoms:**
```
OSError: Can't load tokenizer
HTTPError: 403 Client Error: Forbidden
Connection timeout downloading model
```

**Solutions:**

1. **Pre-download the model:**
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('sentence-transformers/e5-base-v2')
   ```

2. **Check internet connection:**
   ```bash
   curl https://huggingface.co
   ```

### Problem 4: Graph Empty After Ingestion

**Symptoms:**
```json
{
  "services": {
    "neo4j": {"nodes": 0},
    "vector_store": {"vectors": 0}
  }
}
```

**Solutions:**

1. **Check ingestion logs** in the terminal where backend is running

2. **Verify data file paths:**
   ```bash
   ls -lh /mnt/data/jira_issues_clean.csv
   ls -lh /mnt/data/jira_issues_rag.jsonl
   ```

3. **Verify Neo4j has data:**
   ```cypher
   MATCH (n) RETURN count(n) AS node_count
   ```

4. **Re-run ingestion:**
   ```bash
   # Clear existing data in Neo4j Browser:
   # MATCH (n) DETACH DELETE n
   
   # Delete FAISS index:
   rm -rf faiss_index/
   
   # Re-run ingestion:
   curl -X POST http://127.0.0.1:8001/ingest
   ```

### Problem 5: Frontend Connection Errors

**Symptoms:**
```
Network Error
Failed to fetch
CORS error
```

**Solutions:**

1. **Verify backend is running:**
   ```bash
   curl http://127.0.0.1:8001/health
   ```

2. **Check VITE_API_URL:**
   ```bash
   cat frontend/.env
   # Should be: VITE_API_URL=http://127.0.0.1:8001
   ```

3. **Restart frontend:**
   ```bash
   # Press Ctrl+C, then:
   npm run dev
   ```

4. **Check browser console** (F12) for detailed error messages

### Problem 6: Slow Query Responses

**Symptoms:**
- Queries take > 15 seconds
- Frontend times out

**Solutions:**

1. **Use GPT-3.5-turbo instead:**
   ```json
   {
     "query": "...",
     "model": "gpt-3.5-turbo"
   }
   ```

2. **Reduce top_k:**
   ```json
   {
     "query": "...",
     "top_k_sections": 5
   }
   ```

3. **Limit graph hops:**
   ```json
   {
     "query": "...",
     "num_hops": 1
   }
   ```

### Problem 7: OpenAI API Errors

**Symptoms:**
```
AuthenticationError: Incorrect API key
RateLimitError: Rate limit exceeded
```

**Solutions:**

1. **Verify API key:**
   ```bash
   cat .env | grep OPENAI_API_KEY
   ```

2. **Test API key:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. **Check quota:** Visit https://platform.openai.com/usage

### Problem 8: Port Already in Use

**Symptoms:**
```
Address already in use: 8001
EADDRINUSE: address already in use :::5173
```

**Solutions:**

```bash
# macOS/Linux - Kill process on port 8001:
lsof -ti :8001 | xargs kill -9

# macOS/Linux - Kill process on port 5173:
lsof -ti :5173 | xargs kill -9

# Windows PowerShell:
Get-Process -Id (Get-NetTCPConnection -LocalPort 8001).OwningProcess | Stop-Process
```

---

## ⚡ Performance

### Backend Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Vector search | 50-100ms | 10K documents |
| Graph traversal | 200-500ms | 1-2 hops |
| LLM generation | 3-8s | GPT-4 |
| **Total query** | **4-9s** | With parallel calls |
| Clustering (100 tickets) | 30-80ms | K-Means fastest, DBSCAN moderate |
| Clustering (500 tickets) | 100-300ms | Varies by algorithm |
| Clustering (1000 tickets) | 200-600ms | Agglomerative slowest |

### Frontend Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Bundle size | ~500KB | Gzipped |
| First load | <2s | 3G connection |
| Subsequent loads | <500ms | Cached |
| Graph rendering | <1s | 100 nodes |

### Optimizations

✅ **Parallel API calls** - Vector + graph fetched simultaneously  
✅ **FAISS IP index** - Inner Product faster than L2  
✅ **Neo4j indexes** - On key properties  
✅ **orjson serialization** - 2-3x faster than standard json  
✅ **Vite HMR** - Fast development iteration  
✅ **Code splitting** - Automatic via Vite  

---

## 🚢 Deployment

### Docker Compose (Production)

The project includes a `docker-compose.yml` file for Neo4j. To deploy the full stack:

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.22.0
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/production_password
      NEO4J_PLUGINS: '["graph-data-science"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

  backend:
    build: ./backend
    ports:
      - "8001:8001"
    depends_on:
      - neo4j
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: production_password
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - faiss_data:/app/faiss_index

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      VITE_API_URL: http://backend:8001

volumes:
  neo4j_data:
  neo4j_logs:
  faiss_data:
```

Start with:
```bash
docker-compose up -d
```

### Environment-Specific Configurations

**Development:**
- `--reload` for auto-reload
- CORS allows localhost
- Verbose logging

**Production:**
- Multiple workers: `--workers 4`
- Restricted CORS origins
- Log to file
- Health monitoring
- SSL/TLS certificates

---

## 🤝 Contributing

### Ways to Extend

1. **Add new data sources**: Create new ingestor in `backend/ingestors/`
2. **Customize prompts**: Edit `backend/llm/prompts.py`
3. **Add graph algorithms**: Update `backend/graph/gds.cypher`
4. **Enhance UI**: Add components in `frontend/src/components/`
5. **Add API endpoints**: Update `backend/app_main.py`

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Use type hints (Python) and TypeScript
- Handle errors gracefully

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with amazing open-source technologies:

- **Neo4j** - Graph database platform
- **Facebook AI FAISS** - Efficient similarity search
- **Hugging Face** - E5 embeddings model
- **OpenAI** - GPT-4 language model
- **FastAPI** - Modern Python web framework
- **React** - UI library
- **Cytoscape.js** - Graph visualization library
- **Tailwind CSS** - Utility-first CSS framework

---

## Support & Resources

### Documentation

- [Backend README](backend/README.md) - Backend setup and API
- [Frontend README](frontend/README.md) - Frontend components
- [API Documentation](backend/API_README.md) - Endpoint details
- [Setup Guide](SETUP_GUIDE.md) - Step-by-step walkthrough
- [Demo Guide](DEMO_GUIDE.md) - Demo usage instructions
- [Clustering Demo Guide](CLUSTERING_DEMO_README.md) - Clustering demo details
- [Graph Module](backend/graph/README.md) - Neo4j operations

### Phase Documentation

Complete implementation notes:
- [PHASE1_COMPLETE.md](Phases/PHASE1_COMPLETE.md) - Environment & Dependencies
- [PHASE2_COMPLETE.md](Phases/PHASE2_COMPLETE.md) - Graph Database
- [PHASE3_COMPLETE.md](Phases/PHASE3_COMPLETE.md) - Ingestion & Embeddings
- [PHASE6_COMPLETE.md](Phases/PHASE6_COMPLETE.md) - Frontend
- [PROJECT_COMPLETE.md](Phases/PROJECT_COMPLETE.md) - Full project summary

### External Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [FAISS GitHub](https://github.com/facebookresearch/faiss)
- [E5 Model on Hugging Face](https://huggingface.co/intfloat/e5-base-v2)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Cytoscape.js Documentation](https://js.cytoscape.org/)

---

## 🎉 Project Status

### ✅ COMPLETE AND PRODUCTION-READY

| Phase | Status | Documentation |
|-------|--------|---------------|
| Phase 1: Environment & Dependencies | ✅ Complete | [PHASE1](Phases/PHASE1_COMPLETE.md) |
| Phase 2: Graph Database (Neo4j + GDS) | ✅ Complete | [PHASE2](Phases/PHASE2_COMPLETE.md) |
| Phase 3: Ingestion + Embeddings | ✅ Complete | [PHASE3](Phases/PHASE3_COMPLETE.md) |
| Phase 4: LLM Prompts + Dual Answers | ✅ Complete | Integrated |
| Phase 5: FastAPI Application | ✅ Complete | Integrated |
| Phase 6: Frontend (Beautiful UI) | ✅ Complete | [PHASE6](Phases/PHASE6_COMPLETE.md) |
| Phase 7: Run & Verify | ✅ Complete | [PHASE7](Phases/PHASE7_COMPLETE.md) |
| Phase 8: Clustering Demo | ✅ Complete | [PHASE8](Phases/PHASE8_COMPLETE.md) |

### System Features

✅ **Backend**: FastAPI + Neo4j + FAISS + E5 + GPT-4  
✅ **Frontend**: React + TypeScript + Tailwind + Cytoscape  
✅ **Clustering Demo**: K-Means, Agglomerative, DBSCAN comparison  
✅ **Cluster Search**: Multi-cluster type search with benchmarking  
✅ **Documentation**: 2000+ lines across 10+ files  
✅ **Troubleshooting**: 8+ scenarios covered  
✅ **Testing**: Manual test checklist provided  
✅ **Deployment**: Docker Compose ready  

---

**Ready to get started?** Follow the [Quick Start](#-quick-start) guide or see [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions!
