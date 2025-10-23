"""
HealthAI Vector Store Module
Handles document indexing and similarity search
"""

from .faiss_store import FAISSVectorStore, HealthAIVectorStore

__all__ = ["FAISSVectorStore", "HealthAIVectorStore"]