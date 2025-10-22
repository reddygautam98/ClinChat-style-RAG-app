from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ClinChat RAG"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # API Keys
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Database
    DATABASE_URL: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"

    # Vector Store
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # RAG Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.1

    # Fusion AI Configuration
    FUSION_AI_ENABLED: bool = True
    FUSION_STRATEGY: str = "weighted_average"  # Options: weighted_average, majority_vote, best_confidence
    GEMINI_WEIGHT: float = 0.6
    GROQ_WEIGHT: float = 0.4
    FUSION_CONFIDENCE_THRESHOLD: float = 0.7
    FUSION_MAX_RETRIES: int = 2

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/clinchat.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()