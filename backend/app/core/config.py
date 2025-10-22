"""Application configuration using env utility."""
from backend.utils.env import env


class Settings:
    """Application settings loaded from environment variables."""
    
    # Neo4j Configuration
    NEO4J_URI: str = env("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = env("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = env("NEO4J_PASSWORD", "password")
    
    # API Configuration
    API_HOST: str = env("APP_HOST", "127.0.0.1")
    API_PORT: int = int(env("APP_PORT", "8000"))
    API_RELOAD: bool = True
    
    # Model Configuration
    EMBEDDING_MODEL: str = env("EMBED_MODEL", "sentence-transformers/e5-base-v2")
    FAISS_INDEX_PATH: str = env("FAISS_INDEX_PATH", "./faiss_index")
    
    # OpenAI (optional)
    OPENAI_API_KEY: str = env("OPENAI_API_KEY", "")
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()

