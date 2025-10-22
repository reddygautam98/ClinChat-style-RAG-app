"""
ClinChat Embeddings Module
Handles text embeddings using multiple providers with fusion capabilities
"""

from .openai_embed import ClinChatEmbedding, EmbeddingProvider, FusionEmbedding

__all__ = ["ClinChatEmbedding", "EmbeddingProvider", "FusionEmbedding"]