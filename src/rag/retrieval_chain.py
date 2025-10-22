"""
RAG Retrieval Chain for ClinChat Application
Combines document retrieval with AI generation for question answering
"""

import os
import sys
from typing import List, Dict, Any, Optional
import logging

# Add src to path for imports
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(src_dir)
sys.path.insert(0, root_dir)
sys.path.insert(0, src_dir)

from src.embeddings.openai_embed import ClinChatEmbedding
from src.vectorstore.faiss_store import ClinChatVectorStore
from src.services.fusion_ai import FusionAIService
from src.ingestion.pdf_parser import PDFParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGRetriever:
    """Document retrieval component for RAG"""
    
    def __init__(self, vector_store: ClinChatVectorStore, embedder: ClinChatEmbedding):
        """
        Initialize RAG retriever
        
        Args:
            vector_store: Vector database for document storage
            embedder: Embedding model for query processing
        """
        self.vector_store = vector_store
        self.embedder = embedder
        
    def retrieve_documents(self, query: str, k: int = 5, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            threshold: Similarity threshold
            
        Returns:
            List of relevant documents with metadata
        """
        logger.info(f"Retrieving documents for query: '{query[:50]}...'")
        
        # Search for relevant documents
        results = self.vector_store.search(query, self.embedder, k=k, threshold=threshold)
        
        logger.info(f"Retrieved {len(results)} documents")
        return results


class RAGGenerator:
    """Text generation component for RAG"""
    
    def __init__(self, ai_service: FusionAIService):
        """
        Initialize RAG generator
        
        Args:
            ai_service: AI service for text generation
        """
        self.ai_service = ai_service
    
    def generate_answer(self, query: str, context_docs: List[Dict[str, Any]], 
                       max_context_length: int = 4000) -> Dict[str, Any]:
        """
        Generate answer using retrieved documents as context
        
        Args:
            query: User question
            context_docs: Retrieved documents
            max_context_length: Maximum context length for AI model
            
        Returns:
            Generated answer with metadata
        """
        # Build context from retrieved documents
        context_parts = []
        total_length = 0
        used_docs = []
        
        for doc in context_docs:
            doc_text = f"Source: {doc.get('source', 'Unknown')}\nContent: {doc.get('text', '')}\n"
            
            if total_length + len(doc_text) > max_context_length:
                break
            
            context_parts.append(doc_text)
            used_docs.append(doc)
            total_length += len(doc_text)
        
        # Combine context
        context = "\n---\n".join(context_parts)
        
        # Create prompt for AI model
        prompt = self._create_prompt(query, context)
        
        # Generate answer using AI service
        logger.info("Generating answer with AI service")
        import asyncio
        response = asyncio.run(self.ai_service.fusion_generate(prompt, context))
        
        # Return answer with metadata
        return {
            "answer": response.final_response,
            "sources": [doc.get('source', 'Unknown') for doc in used_docs],
            "confidence": response.confidence_score,
            "context_used": len(used_docs),
            "model_used": response.fusion_strategy,
            "fusion_details": response.processing_details
        }
    
    def _create_prompt(self, query: str, context: str) -> str:
        """
        Create prompt for AI model
        
        Args:
            query: User question
            context: Retrieved document context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are a helpful medical AI assistant. Use the provided context to answer the user's question accurately and comprehensively.

Context from medical documents:
{context}

User Question: {query}

Instructions:
1. Answer based primarily on the provided context
2. If the context doesn't contain relevant information, say so clearly
3. Provide specific, actionable medical information when possible
4. Include disclaimers about consulting healthcare professionals for serious concerns
5. Be concise but thorough

Answer:"""
        
        return prompt


class ClinChatRAG:
    """Complete RAG system for ClinChat application"""
    
    def __init__(self, vectorstore_path: str = "data/vectorstore"):
        """
        Initialize ClinChat RAG system
        
        Args:
            vectorstore_path: Path to vector database storage
        """
        self.vectorstore_path = vectorstore_path
        
        # Initialize components
        logger.info("Initializing ClinChat RAG system...")
        
        try:
            # Initialize embedding system
            self.embedder = ClinChatEmbedding()
            logger.info("✅ Embedding system initialized")
            
            # Initialize vector store
            self.vector_store = ClinChatVectorStore(vectorstore_path)
            logger.info("✅ Vector store initialized")
            
            # Initialize retriever
            self.retriever = RAGRetriever(self.vector_store, self.embedder)
            logger.info("✅ Retriever initialized")
            
            # Initialize AI service for generation
            self.ai_service = FusionAIService()
            logger.info("✅ AI service initialized")
            
            # Initialize generator
            self.generator = RAGGenerator(self.ai_service)
            logger.info("✅ Generator initialized")
            
            logger.info("🎉 ClinChat RAG system ready!")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    def index_documents(self, pdf_directory: str) -> Dict[str, Any]:
        """
        Index all PDF documents from a directory
        
        Args:
            pdf_directory: Directory containing PDF files
            
        Returns:
            Indexing statistics
        """
        logger.info(f"Indexing documents from {pdf_directory}")
        
        try:
            # Initialize PDF parser
            parser = PDFParser(chunk_size=1000, chunk_overlap=200)
            
            # Process all PDFs
            chunks = parser.process_multiple_pdfs(pdf_directory)
            
            if not chunks:
                logger.warning("No chunks extracted from PDFs")
                return {"status": "error", "message": "No content extracted"}
            
            # Generate embeddings for chunks
            enriched_chunks = self.embedder.embed_chunks(chunks)
            
            # Index in vector store
            self.vector_store.index_documents(enriched_chunks)
            
            # Get statistics
            stats = self.vector_store.get_stats()
            
            logger.info(f"Successfully indexed {len(chunks)} chunks from {pdf_directory}")
            
            return {
                "status": "success",
                "chunks_processed": len(chunks),
                "total_documents": stats["total_documents"],
                "vectorstore_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return {"status": "error", "message": str(e)}
    
    def query(self, question: str, k: int = 5, threshold: float = 0.1) -> Dict[str, Any]:
        """
        Query the RAG system with a question
        
        Args:
            question: User question
            k: Number of documents to retrieve
            threshold: Similarity threshold for retrieval
            
        Returns:
            Answer with sources and metadata
        """
        logger.info(f"Processing query: '{question[:50]}...'")
        
        try:
            # Check if vector store has documents
            stats = self.vector_store.get_stats()
            if stats["total_documents"] == 0:
                return {
                    "answer": "I don't have any indexed documents to search. Please index some medical documents first.",
                    "sources": [],
                    "confidence": 0.0,
                    "status": "no_documents"
                }
            
            # Retrieve relevant documents
            retrieved_docs = self.retriever.retrieve_documents(question, k=k, threshold=threshold)
            
            if not retrieved_docs:
                return {
                    "answer": "I couldn't find any relevant information in the indexed documents for your question.",
                    "sources": [],
                    "confidence": 0.0,
                    "status": "no_results"
                }
            
            # Generate answer using retrieved context
            result = self.generator.generate_answer(question, retrieved_docs)
            result["status"] = "success"
            result["retrieved_docs"] = len(retrieved_docs)
            
            logger.info(f"Successfully answered query using {len(retrieved_docs)} documents")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "status": "error"
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            vector_stats = self.vector_store.get_stats()
            import asyncio
            ai_stats = asyncio.run(self.ai_service.get_fusion_health_status())
            
            return {
                "vectorstore": vector_stats,
                "ai_service": ai_stats,
                "embedder_status": "active" if self.embedder else "inactive",
                "system_status": "ready"
            }
        except Exception as e:
            return {
                "system_status": "error",
                "error": str(e)
            }


def test_rag_system():
    """Test the complete RAG system"""
    print("🧠 Testing ClinChat RAG System")
    print("=" * 50)
    
    try:
        # Initialize RAG system
        rag = ClinChatRAG(vectorstore_path="test_rag_vectorstore")
        
        # Create sample documents for testing
        sample_chunks = [
            {
                "text": "Diabetes mellitus is a chronic condition characterized by high blood glucose levels. It requires careful management through diet, exercise, and medication.",
                "source": "diabetes_guide.pdf",
                "chunk_index": 0
            },
            {
                "text": "Type 2 diabetes is the most common form, often developing in adults over 40. It can often be managed with lifestyle changes and oral medications.",
                "source": "diabetes_guide.pdf",
                "chunk_index": 1
            },
            {
                "text": "Hypertension, or high blood pressure, is a major risk factor for heart disease and stroke. Regular monitoring and medication can help control it.",
                "source": "hypertension_info.pdf",
                "chunk_index": 0
            }
        ]
        
        # Generate embeddings and index documents
        print("Indexing sample documents...")
        enriched_chunks = rag.embedder.embed_chunks(sample_chunks)
        rag.vector_store.index_documents(enriched_chunks)
        
        print(f"✅ Indexed {len(enriched_chunks)} chunks")
        
        # Test queries
        test_queries = [
            "What is diabetes?",
            "How to manage high blood pressure?", 
            "What are the symptoms of type 2 diabetes?"
        ]
        
        print("\nTesting RAG queries...")
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            result = rag.query(query, k=2, threshold=0.0)
            
            print(f"   Answer: {result['answer'][:100]}...")
            print(f"   Sources: {result['sources']}")
            print(f"   Status: {result['status']}")
        
        # Test system stats
        stats = rag.get_system_stats()
        print(f"\n📊 System Stats: {stats}")
        
        print("\n✅ RAG system test completed successfully!")
        
        # Clean up
        import shutil
        from pathlib import Path
        test_dir = Path("test_rag_vectorstore")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        
    except Exception as e:
        print(f"❌ RAG system test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_rag_system()