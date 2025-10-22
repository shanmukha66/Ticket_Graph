# Graph RAG Backend

FastAPI backend for Graph RAG application with Neo4j, sentence-transformers, and FAISS.

## Features

- **FastAPI** - Modern Python web framework
- **Neo4j** - Graph database with GDS support
- **Sentence Transformers** - E5 embeddings model
- **FAISS** - Local vector search (CPU-based)
- **Pydantic v2** - Data validation
- **NetworkX** - Graph algorithms

## Prerequisites

- Python 3.10 or higher
- Neo4j database running (default: bolt://localhost:7687)

## Setup

### 1. Create and Activate Virtual Environment

From the backend directory:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

Or if you're already in the backend directory:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the **project root** (not in backend/):

```bash
# From project root
cp .env.example .env
```

Then edit `.env` with your actual values:
- Add your Neo4j credentials (NEO4J_USER, NEO4J_PASSWORD, NEO4J_URI)
- Set EMBED_MODEL if you want a different model
- Configure FAISS_INDEX_PATH for index storage
- Add OPENAI_API_KEY if using OpenAI

**Important**: The .env file must be created manually by you, not by Cursor.

## Running the Server

### Development Mode (with auto-reload)

From the project root:

```bash
uvicorn backend.app.main:app --reload --host $APP_HOST --port $APP_PORT
```

Or using environment variables directly:

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Using the run script

From the backend directory:

```bash
python run.py
```

## API Endpoints

The API will be available at:
- API: http://127.0.0.1:8000
- Interactive Docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API Endpoints

### Graph Operations
- `POST /api/graph/nodes` - Create a node
- `POST /api/graph/relationships` - Create a relationship
- `GET /api/graph/` - Get all nodes and relationships
- `POST /api/graph/communities` - Run community detection
- `DELETE /api/graph/` - Clear graph

### Search Operations
- `POST /api/search/` - Semantic search
- `POST /api/search/index` - Index documents
- `DELETE /api/search/` - Clear index

### Embeddings
- `POST /api/embeddings/` - Generate embedding
- `GET /api/embeddings/info` - Model information

## Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Configuration
│   ├── models/        # Pydantic schemas
│   └── services/      # Business logic
├── requirements.txt
└── README.md
```

