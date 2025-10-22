"""
ClinChat Vector Store Module
Handles document indexing and similarity search
"""

from .faiss_store import FAISSVectorStore, ClinChatVectorStore

__all__ = ["FAISSVectorStore", "ClinChatVectorStore"]