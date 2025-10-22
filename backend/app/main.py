"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import graph, search, embeddings
from app.core.config import settings
from app.services.neo4j_service import neo4j_service
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    # Startup
    print("Starting up Graph RAG application...")
    neo4j_service.connect()
    embedding_service.load_model()
    faiss_service.initialize()
    yield
    # Shutdown
    print("Shutting down Graph RAG application...")
    neo4j_service.close()


app = FastAPI(
    title="Graph RAG API",
    description="Graph-based Retrieval Augmented Generation API with Neo4j and FAISS",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(embeddings.router, prefix="/api/embeddings", tags=["embeddings"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Graph RAG API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "neo4j": neo4j_service.is_connected(),
        "embedding_model": embedding_service.is_loaded(),
        "faiss": faiss_service.is_initialized(),
    }

