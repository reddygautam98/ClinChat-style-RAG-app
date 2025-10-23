"""
Embeddings Module for HealthAI RAG Application
Creates text embeddings using Google Gemini and Groq APIs with fusion capabilities
"""

import os
import numpy as np
from typing import List, Dict, Optional, Union
import logging
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Base class for embedding providers"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text"""
        raise NotImplementedError
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return [self.embed_text(text) for text in texts]


class SentenceTransformerProvider(EmbeddingProvider):
    """Sentence Transformers embedding provider (local model)"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__(model_name)
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded SentenceTransformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text"""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batched for efficiency)"""
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini embedding provider"""
    
    def __init__(self, api_key: str, model_name: str = "models/embedding-001"):
        super().__init__(model_name)
        try:
            genai.configure(api_key=api_key)
            self.client = genai
            logger.info(f"Initialized Gemini embedding provider: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini embedding provider: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text"""
        try:
            result = self.client.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating Gemini embedding: {e}")
            # Fallback to sentence transformers if Gemini fails
            fallback = SentenceTransformerProvider()
            return fallback.embed_text(text)


class FusionEmbedding:
    """Fusion embedding system combining multiple embedding providers"""
    
    def __init__(self, providers: List[EmbeddingProvider], weights: Optional[List[float]] = None):
        """
        Initialize fusion embedding system
        
        Args:
            providers: List of embedding providers
            weights: Optional weights for each provider (must sum to 1.0)
        """
        self.providers = providers
        
        if weights is None:
            # Equal weights if not specified
            weights = [1.0 / len(providers)] * len(providers)
        
        if len(weights) != len(providers):
            raise ValueError("Number of weights must match number of providers")
        
        if abs(sum(weights) - 1.0) > 1e-6:
            raise ValueError("Weights must sum to 1.0")
        
        self.weights = weights
        logger.info(f"Initialized fusion embedding with {len(providers)} providers")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate fusion embeddings for a single text"""
        embeddings = []
        
        for provider in self.providers:
            try:
                embedding = provider.embed_text(text)
                embeddings.append(np.array(embedding))
            except Exception as e:
                logger.warning(f"Provider {provider.model_name} failed: {e}")
                continue
        
        if not embeddings:
            raise RuntimeError("All embedding providers failed")
        
        # Normalize embeddings to same dimension if needed
        min_dim = min(len(emb) for emb in embeddings)
        normalized_embeddings = [emb[:min_dim] for emb in embeddings]
        
        # Weighted average of embeddings
        fusion_embedding = np.zeros(min_dim)
        total_weight = 0
        
        for i, embedding in enumerate(normalized_embeddings):
            if i < len(self.weights):
                fusion_embedding += self.weights[i] * embedding
                total_weight += self.weights[i]
        
        # Normalize by total weight (in case some providers failed)
        if total_weight > 0:
            fusion_embedding /= total_weight
        
        return fusion_embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate fusion embeddings for multiple texts"""
        return [self.embed_text(text) for text in texts]


class HealthAIEmbedding:
    """Main embedding class for HealthAI application"""
    
    def __init__(self):
        """Initialize HealthAI embedding system"""
        self.providers = []
        self.fusion_embedding = None
        
        # Load API keys from environment
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        
        # Initialize available providers
        providers = []
        
        # Always include Sentence Transformers as fallback
        try:
            st_provider = SentenceTransformerProvider("all-MiniLM-L6-v2")
            providers.append(st_provider)
            logger.info("✅ SentenceTransformer provider initialized")
        except Exception as e:
            logger.warning(f"SentenceTransformer provider failed: {e}")
        
        # Add Gemini provider if API key is available
        if gemini_api_key:
            try:
                gemini_provider = GeminiEmbeddingProvider(gemini_api_key)
                providers.append(gemini_provider)
                logger.info("✅ Gemini embedding provider initialized")
            except Exception as e:
                logger.warning(f"Gemini embedding provider failed: {e}")
        
        if not providers:
            raise RuntimeError("No embedding providers could be initialized")
        
        # Create fusion embedding system
        if len(providers) > 1:
            # Weight Gemini higher if available, otherwise equal weights
            if len(providers) == 2:  # SentenceTransformer + Gemini
                weights = [0.4, 0.6]  # Favor Gemini
            else:
                weights = [1.0 / len(providers)] * len(providers)
            
            self.fusion_embedding = FusionEmbedding(providers, weights)
            logger.info(f"✅ Fusion embedding initialized with {len(providers)} providers")
        else:
            # Single provider
            self.fusion_embedding = providers[0]
            logger.info(f"✅ Single provider embedding initialized: {providers[0].model_name}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        return self.fusion_embedding.embed_text(text.strip())
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts provided")
        
        return self.fusion_embedding.embed_texts(valid_texts)
    
    def embed_chunks(self, chunks: List[Dict[str, str]]) -> List[Dict[str, Union[str, List[float]]]]:
        """
        Generate embeddings for text chunks from PDF parser
        
        Args:
            chunks: List of chunk dictionaries with 'text' key
            
        Returns:
            List of chunks with added 'embedding' key
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Add embeddings to chunks
        enriched_chunks = []
        for i, chunk in enumerate(chunks):
            enriched_chunk = chunk.copy()
            enriched_chunk['embedding'] = embeddings[i]
            enriched_chunk['embedding_dim'] = len(embeddings[i])
            enriched_chunks.append(enriched_chunk)
        
        logger.info(f"✅ Generated embeddings for {len(enriched_chunks)} chunks")
        return enriched_chunks


def test_embeddings():
    """Test the embedding system"""
    print("🧪 Testing HealthAI Embedding System")
    print("=" * 50)
    
    try:
        # Initialize embedding system
        embedder = HealthAIEmbedding()
        
        # Test single text embedding
        test_text = "Diabetes is a chronic condition that affects blood sugar levels."
        print(f"Test text: {test_text}")
        
        embedding = embedder.embed_text(test_text)
        print(f"✅ Embedding generated - Dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        
        # Test multiple texts
        test_texts = [
            "High blood pressure can lead to heart disease.",
            "Regular exercise helps control diabetes.",
            "Proper medication adherence is crucial for patient outcomes."
        ]
        
        print(f"\nTesting {len(test_texts)} texts...")
        embeddings = embedder.embed_texts(test_texts)
        print(f"✅ Batch embeddings generated - {len(embeddings)} embeddings")
        
        # Test chunk embeddings
        sample_chunks = [
            {
                "text": "Insulin therapy is essential for type 1 diabetes management.",
                "source": "test_doc.pdf",
                "chunk_index": 0
            },
            {
                "text": "Blood glucose monitoring helps track treatment effectiveness.",
                "source": "test_doc.pdf",
                "chunk_index": 1
            }
        ]
        
        print("\nTesting chunk embeddings...")
        enriched_chunks = embedder.embed_chunks(sample_chunks)
        print(f"✅ Chunk embeddings generated - {len(enriched_chunks)} chunks enriched")
        
        for i, chunk in enumerate(enriched_chunks):
            print(f"Chunk {i+1}: {len(chunk['embedding'])} dimensional embedding")
        
        print("\n✅ All embedding tests passed!")
        
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_embeddings()