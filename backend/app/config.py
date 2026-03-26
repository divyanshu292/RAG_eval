from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    mongodb_uri: str = "mongodb://mongodb:27017/rag_service"
    qdrant_url: str = "http://qdrant:6333"

    # Model configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    generation_model: str = "gpt-5.4"
    evaluation_model: str = "gpt-5.4"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retrieval
    top_k: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
