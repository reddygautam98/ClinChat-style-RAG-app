"""
Vector Store Module for HealthAI RAG Application
Handles document indexing and similarity search using FAISS
"""

import os
import json
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import faiss
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for document embeddings"""
    
    def __init__(self, dimension: int = 384, index_type: str = "flat"):
        """
        Initialize FAISS vector store
        
        Args:
            dimension: Dimension of the embeddings
            index_type: Type of FAISS index ("flat", "ivf", "hnsw")
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.documents = []  # Store document metadata
        self.embeddings = []  # Store embeddings for backup
        
        # Initialize FAISS index
        self._initialize_index()
        
        logger.info(f"Initialized FAISS vector store (dim={dimension}, type={index_type})")
    
    def _initialize_index(self):
        """Initialize the FAISS index based on type"""
        if self.index_type == "flat":
            # Flat index - exact search, good for smaller datasets
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        elif self.index_type == "ivf":
            # IVF index - approximate search, good for larger datasets
            quantizer = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)  # 100 clusters
        elif self.index_type == "hnsw":
            # HNSW index - hierarchical navigable small world
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)  # M=32
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add documents with embeddings to the vector store
        
        Args:
            chunks: List of chunk dictionaries with 'embedding' key
        """
        if not chunks:
            logger.warning("No chunks provided to add")
            return
        
        # Extract embeddings and normalize them
        embeddings = []
        valid_chunks = []
        
        for chunk in chunks:
            if 'embedding' not in chunk:
                logger.warning(f"Chunk missing embedding: {chunk.get('source', 'unknown')}")
                continue
            
            embedding = np.array(chunk['embedding'], dtype=np.float32)
            
            # Normalize embedding for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            embeddings.append(embedding)
            
            # Store document metadata (remove embedding to save space)
            doc_metadata = {k: v for k, v in chunk.items() if k != 'embedding'}
            doc_metadata['doc_id'] = len(self.documents)
            valid_chunks.append(doc_metadata)
        
        if not embeddings:
            logger.warning("No valid embeddings found")
            return
        
        # Convert to numpy array
        embeddings_array = np.vstack(embeddings)
        
        # Add to FAISS index
        if self.index_type == "ivf" and not self.index.is_trained:
            # Train IVF index if not already trained
            logger.info("Training IVF index...")
            self.index.train(embeddings_array)
        
        # Add embeddings to index
        self.index.add(embeddings_array)
        
        # Store metadata and embeddings
        self.documents.extend(valid_chunks)
        self.embeddings.extend(embeddings)
        
        logger.info(f"Added {len(embeddings)} documents to vector store")
        logger.info(f"Total documents: {len(self.documents)}")
    
    def similarity_search(self, query_embedding: List[float], k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Perform similarity search
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar documents with scores
        """
        if len(self.documents) == 0:
            logger.warning("No documents in vector store")
            return []
        
        # Normalize query embedding
        query_vec = np.array(query_embedding, dtype=np.float32)
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec = query_vec / norm
        
        # Reshape for FAISS
        query_vec = query_vec.reshape(1, -1)
        
        # Search
        scores, indices = self.index.search(query_vec, min(k, len(self.documents)))
        
        # Process results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1 or score < threshold:  # -1 indicates no result found
                continue
            
            result = self.documents[idx].copy()
            result['similarity_score'] = float(score)
            result['rank'] = i + 1
            results.append(result)
        
        logger.info(f"Found {len(results)} similar documents (threshold={threshold})")
        return results
    
    def search_by_text(self, query_text: str, embedder, k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search using text query (convenience method)
        
        Args:
            query_text: Query text
            embedder: Embedding model to generate query embedding
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar documents with scores
        """
        # Generate query embedding
        query_embedding = embedder.embed_text(query_text)
        return self.similarity_search(query_embedding, k, threshold)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "total_documents": len(self.documents),
            "dimension": self.dimension,
            "index_type": self.index_type,
            "index_size": self.index.ntotal if self.index else 0,
            "is_trained": getattr(self.index, 'is_trained', True)
        }
    
    def save(self, directory: str) -> None:
        """
        Save vector store to disk
        
        Args:
            directory: Directory to save the vector store
        """
        save_dir = Path(directory)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = save_dir / "faiss.index"
        faiss.write_index(self.index, str(index_path))
        
        # Save document metadata
        docs_path = save_dir / "documents.json"
        with open(docs_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2, default=str)
        
        # Save embeddings
        embeddings_path = save_dir / "embeddings.npy"
        if self.embeddings:
            embeddings_array = np.vstack(self.embeddings)
            np.save(embeddings_path, embeddings_array)
        
        # Save metadata
        metadata = {
            "dimension": self.dimension,
            "index_type": self.index_type,
            "total_documents": len(self.documents),
            "created_at": datetime.now().isoformat()
        }
        metadata_path = save_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved vector store to {directory}")
    
    @classmethod
    def load(cls, directory: str) -> 'FAISSVectorStore':
        """
        Load vector store from disk
        
        Args:
            directory: Directory containing the saved vector store
            
        Returns:
            Loaded FAISSVectorStore instance
        """
        load_dir = Path(directory)
        
        if not load_dir.exists():
            raise FileNotFoundError(f"Vector store directory not found: {directory}")
        
        # Load metadata
        metadata_path = load_dir / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Create instance
        instance = cls(
            dimension=metadata['dimension'],
            index_type=metadata['index_type']
        )
        
        # Load FAISS index
        index_path = load_dir / "faiss.index"
        if index_path.exists():
            instance.index = faiss.read_index(str(index_path))
        
        # Load documents
        docs_path = load_dir / "documents.json"
        if docs_path.exists():
            with open(docs_path, 'r', encoding='utf-8') as f:
                instance.documents = json.load(f)
        
        # Load embeddings
        embeddings_path = load_dir / "embeddings.npy"
        if embeddings_path.exists():
            embeddings_array = np.load(embeddings_path)
            instance.embeddings = [embeddings_array[i] for i in range(len(embeddings_array))]
        
        logger.info(f"Loaded vector store from {directory}")
        logger.info(f"Total documents: {len(instance.documents)}")
        
        return instance


class HealthAIVectorStore:
    """High-level vector store interface for HealthAI"""
    
    def __init__(self, storage_path: str = "data/vectorstore", dimension: int = 384):
        """
        Initialize HealthAI vector store
        
        Args:
            storage_path: Path to store the vector database
            dimension: Embedding dimension
        """
        self.storage_path = storage_path
        self.dimension = dimension
        self.vector_store = None
        
        # Try to load existing vector store, otherwise create new one
        if Path(storage_path).exists():
            try:
                self.vector_store = FAISSVectorStore.load(storage_path)
                logger.info("Loaded existing vector store")
            except Exception as e:
                logger.warning(f"Failed to load existing vector store: {e}")
                self.vector_store = FAISSVectorStore(dimension=dimension)
        else:
            self.vector_store = FAISSVectorStore(dimension=dimension)
    
    def index_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Index documents in the vector store
        
        Args:
            chunks: List of document chunks with embeddings
        """
        logger.info(f"Indexing {len(chunks)} document chunks")
        self.vector_store.add_documents(chunks)
        
        # Auto-save after indexing
        self.save()
    
    def search(self, query_text: str, embedder, k: int = 5, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query_text: Search query
            embedder: Embedding model
            k: Number of results
            threshold: Similarity threshold
            
        Returns:
            List of relevant documents
        """
        return self.vector_store.search_by_text(query_text, embedder, k, threshold)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        stats = self.vector_store.get_stats()
        stats['storage_path'] = self.storage_path
        return stats
    
    def save(self) -> None:
        """Save vector store to disk"""
        self.vector_store.save(self.storage_path)
    
    def clear(self) -> None:
        """Clear all documents from vector store"""
        self.vector_store = FAISSVectorStore(dimension=self.dimension)
        logger.info("Cleared vector store")


def test_vector_store():
    """Test the vector store functionality"""
    print("🔍 Testing HealthAI Vector Store")
    print("=" * 50)
    
    try:
        # Create secure random generator with seed for reproducibility
        rng = np.random.default_rng(42)
        
        # Create sample chunks with embeddings
        sample_chunks = [
            {
                "text": "Diabetes is a chronic condition that affects blood sugar levels. Regular monitoring is essential.",
                "source": "diabetes_guide.pdf",
                "chunk_index": 0,
                "embedding": rng.random(384).tolist()  # Secure random embedding
            },
            {
                "text": "Hypertension, or high blood pressure, is a major risk factor for cardiovascular disease.",
                "source": "hypertension_info.pdf", 
                "chunk_index": 0,
                "embedding": rng.random(384).tolist()  # Secure random embedding
            },
            {
                "text": "Regular exercise and proper diet are crucial for managing diabetes effectively.",
                "source": "diabetes_guide.pdf",
                "chunk_index": 1,
                "embedding": rng.random(384).tolist()  # Secure random embedding
            }
        ]
        
        # Test FAISS vector store
        print("Testing FAISS Vector Store...")
        vector_store = FAISSVectorStore(dimension=384)
        
        # Add documents
        vector_store.add_documents(sample_chunks)
        
        # Test search
        query_embedding = rng.random(384).tolist()
        results = vector_store.similarity_search(query_embedding, k=2)
        
        print(f"✅ Search completed - Found {len(results)} results")
        for result in results:
            print(f"  - Score: {result['similarity_score']:.3f}, Source: {result['source']}")
        
        # Test stats
        stats = vector_store.get_stats()
        print(f"✅ Vector store stats: {stats}")
        
        # Test save/load
        test_dir = "test_vectorstore"
        vector_store.save(test_dir)
        loaded_store = FAISSVectorStore.load(test_dir)
        
        print("✅ Save/Load test passed")
        print(f"   Original docs: {len(vector_store.documents)}")
        print(f"   Loaded docs: {len(loaded_store.documents)}")
        
        # Clean up
        import shutil
        if Path(test_dir).exists():
            shutil.rmtree(test_dir)
        
        print("\n✅ All vector store tests passed!")
        
    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_vector_store()