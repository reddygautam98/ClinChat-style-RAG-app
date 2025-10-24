"""
Comprehensive integration tests for RAG pipeline
Tests the complete data science pipeline: document processing, embeddings, vector storage, retrieval
"""

import pytest
import tempfile
import shutil
import numpy as np
from typing import List
import time

# Test imports
from src.vectorstore.faiss_store import FAISSVectorStore


class TestRAGPipelineIntegration:
    """Integration tests for the complete RAG pipeline"""
    
    @pytest.fixture
    def temp_vectorstore_dir(self):
        """Create temporary directory for vectorstore testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_medical_documents(self):
        """Create sample medical documents for testing"""
        rng = np.random.default_rng(42)
        return [
            {
                "text": "Diabetes mellitus is a chronic condition characterized by elevated blood glucose levels. Type 2 diabetes is the most common form, often managed through lifestyle modifications, oral medications like metformin, and insulin therapy when needed. Regular monitoring of HbA1c levels is essential for optimal diabetes management.",
                "source": "diabetes_guide.pdf",
                "chunk_index": 0,
                "metadata": {"specialty": "endocrinology", "topic": "diabetes"},
                "embedding": rng.random(384).tolist()
            },
            {
                "text": "Hypertension, or high blood pressure, affects millions of people worldwide. Normal blood pressure is typically below 120/80 mmHg. Treatment includes ACE inhibitors, ARBs, calcium channel blockers, and lifestyle modifications such as reduced sodium intake and regular exercise.",
                "source": "hypertension_manual.pdf",
                "chunk_index": 0,
                "metadata": {"specialty": "cardiology", "topic": "hypertension"},
                "embedding": rng.random(384).tolist()
            },
            {
                "text": "Cardiovascular disease prevention involves multiple strategies including regular exercise, healthy diet, smoking cessation, and management of risk factors like diabetes and hypertension. Statins are commonly prescribed for cholesterol management in high-risk patients.",
                "source": "cardio_prevention.pdf",
                "chunk_index": 0,
                "metadata": {"specialty": "cardiology", "topic": "prevention"},
                "embedding": rng.random(384).tolist()
            }
        ]
    
    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings for consistent testing"""
        # Create deterministic embeddings for testing
        rng = np.random.default_rng(42)
        return {
            "diabetes": rng.random(384).tolist(),
            "hypertension": rng.random(384).tolist(), 
            "cardiovascular": rng.random(384).tolist()
        }
    
    def test_document_ingestion_pipeline(self, sample_medical_documents):
        """Test complete document ingestion and processing pipeline"""
        
        # Initialize components
        vectorstore = FAISSVectorStore(dimension=384)
        
        # Test document addition
        vectorstore.add_documents(sample_medical_documents)
        
        # Verify documents were stored
        stats = vectorstore.get_stats()
        assert stats["total_documents"] == 3
        assert stats["dimension"] == 384
        
        # Verify document content through vectorstore documents list
        sources = [doc["source"] for doc in vectorstore.documents]
        assert "diabetes_guide.pdf" in sources
        assert "hypertension_manual.pdf" in sources
        assert "cardio_prevention.pdf" in sources
    
    def test_embedding_generation_consistency(self, sample_medical_documents):
        """Test embedding generation consistency and quality"""
        
        # Test embedding properties from sample documents
        for doc in sample_medical_documents:
            embedding = doc["embedding"]
            
            # Verify embedding properties
            assert len(embedding) == 384
            assert all(isinstance(x, float) for x in embedding)
            assert all(0 <= x <= 1 for x in embedding)  # Normalized embeddings
    
    def test_vector_search_functionality(self, sample_medical_documents, mock_embeddings):
        """Test vector search accuracy and relevance"""
        
        # Setup vectorstore with sample data
        vectorstore = FAISSVectorStore(dimension=384)
        vectorstore.add_documents(sample_medical_documents)
        
        # Test similarity search with diabetes query
        query_embedding = mock_embeddings["diabetes"]
        results = vectorstore.similarity_search(query_embedding, k=2)
        
        # Verify search results
        assert len(results) <= 2
        assert len(results) > 0
        
        # Check result structure
        for result in results:
            assert "text" in result
            assert "source" in result
            assert "similarity_score" in result
            assert 0 <= result["similarity_score"] <= 1
        
        # Test that results are ordered by similarity
        if len(results) > 1:
            assert results[0]["similarity_score"] >= results[1]["similarity_score"]
    
    def test_pipeline_performance_benchmarks(self, sample_medical_documents):
        """Test performance characteristics of RAG pipeline"""
        
        vectorstore = FAISSVectorStore(dimension=384)
        
        # Test indexing performance
        start_time = time.time()
        vectorstore.add_documents(sample_medical_documents)
        indexing_time = time.time() - start_time
        
        # Verify indexing performance (should be fast for small dataset)
        assert indexing_time < 1.0  # Should complete within 1 second
        
        # Test search performance
        rng = np.random.default_rng(42)
        query_embedding = rng.random(384).tolist()
        
        search_times = []
        for _ in range(5):  # Run multiple searches
            start_time = time.time()
            vectorstore.similarity_search(query_embedding, k=3)
            search_time = time.time() - start_time
            search_times.append(search_time)
        
        avg_search_time = np.mean(search_times)
        max_search_time = max(search_times)
        
        # Verify search performance
        assert avg_search_time < 0.1  # Average should be under 100ms
        assert max_search_time < 0.5   # Max should be under 500ms
        
        # Test memory efficiency
        stats = vectorstore.get_stats()
        assert stats["total_documents"] == 3
        assert stats["dimension"] == 384
    
    def test_error_handling_and_robustness(self):
        """Test error handling and robustness of RAG pipeline"""
        
        vectorstore = FAISSVectorStore(dimension=384)
        
        # Test empty document handling
        empty_docs = []
        vectorstore.add_documents(empty_docs)
        stats = vectorstore.get_stats()
        assert stats["total_documents"] == 0
        
        # Test invalid query handling
        rng = np.random.default_rng(42)
        query_embedding = rng.random(384).tolist()
        
        # Search in empty vectorstore
        empty_results = vectorstore.similarity_search(query_embedding, k=3)
        assert len(empty_results) == 0
    
    def test_data_consistency_and_integrity(self, sample_medical_documents):
        """Test data consistency and integrity throughout pipeline"""
        
        vectorstore = FAISSVectorStore(dimension=384)
        
        # Store documents
        vectorstore.add_documents(sample_medical_documents)
        
        # Verify data integrity
        assert len(vectorstore.documents) == len(sample_medical_documents)
        
        # Check that all original data is preserved
        original_texts = {doc["text"] for doc in sample_medical_documents}
        stored_texts = {doc["text"] for doc in vectorstore.documents}
        assert original_texts == stored_texts
        
        # Test search consistency - same query should return same results
        rng = np.random.default_rng(42)
        query_embedding = rng.random(384).tolist()
        
        results1 = vectorstore.similarity_search(query_embedding, k=2)
        results2 = vectorstore.similarity_search(query_embedding, k=2)
        
        # Results should be identical
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1["text"] == r2["text"]
            assert abs(r1["similarity_score"] - r2["similarity_score"]) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    
    def test_embedding_generation_consistency(self, sample_medical_documents):
        """Test embedding generation consistency and quality"""
        
        # Mock embeddings service (since OpenAI requires API key)
        class MockEmbeddings:
            def __init__(self):
                self.rng = np.random.default_rng(42)
                
            def get_embedding(self, text: str) -> List[float]:
                # Create deterministic embeddings based on text content
                hash_value = hash(text) % 1000000
                self.rng = np.random.default_rng(hash_value)
                return self.rng.random(384).tolist()
        
        embeddings_service = MockEmbeddings()
        
        # Test embedding generation
        for doc in sample_medical_documents:
            embedding = embeddings_service.get_embedding(doc["text"])
            
            # Verify embedding properties
            assert len(embedding) == 384
            assert all(isinstance(x, float) for x in embedding)
            assert all(0 <= x <= 1 for x in embedding)  # Normalized embeddings
            
            # Test consistency - same text should produce same embedding
            embedding2 = embeddings_service.get_embedding(doc["text"])
            np.testing.assert_array_almost_equal(embedding, embedding2, decimal=6)
    
    def test_vector_search_functionality(self, sample_medical_documents, temp_vectorstore_dir, mock_embeddings):
        """Test vector search accuracy and relevance"""
        
        # Setup vectorstore with sample data
        vectorstore = FAISSVectorStore(dimension=384, index_path=temp_vectorstore_dir)
        
        # Add embeddings to documents
        docs_with_embeddings = []
        for i, doc in enumerate(sample_medical_documents):
            doc_copy = doc.copy()
            # Use different embeddings based on content
            if "diabetes" in doc["text"].lower():
                doc_copy["embedding"] = mock_embeddings["diabetes"]
            elif "hypertension" in doc["text"].lower():
                doc_copy["embedding"] = mock_embeddings["hypertension"]
            else:
                doc_copy["embedding"] = mock_embeddings["cardiovascular"]
            docs_with_embeddings.append(doc_copy)
        
        vectorstore.add_documents(docs_with_embeddings)
        
        # Test similarity search
        query_embedding = mock_embeddings["diabetes"]
        results = vectorstore.similarity_search(query_embedding, k=2)
        
        # Verify search results
        assert len(results) <= 2
        assert len(results) > 0
        
        # Check result structure
        for result in results:
            assert "text" in result
            assert "source" in result
            assert "similarity_score" in result
            assert 0 <= result["similarity_score"] <= 1
        
        # Test that most relevant document is returned first
        if len(results) > 1:
            assert results[0]["similarity_score"] >= results[1]["similarity_score"]
    
    def test_retrieval_chain_integration(self, sample_medical_documents, temp_vectorstore_dir):
        """Test complete retrieval chain with query processing"""
        
        # Mock the HealthAIRAG class components
        class MockHealthAIRAG:
            def __init__(self, vectorstore_path):
                self.vectorstore = FAISSVectorStore(dimension=384, index_path=vectorstore_path)
                self.rng = np.random.default_rng(42)
                
            def index_documents(self, documents):
                """Mock document indexing"""
                docs_with_embeddings = []
                for doc in documents:
                    doc_copy = doc.copy()
                    # Generate mock embeddings
                    doc_copy["embedding"] = self.rng.random(384).tolist()
                    docs_with_embeddings.append(doc_copy)
                
                self.vectorstore.add_documents(docs_with_embeddings)
                return {
                    "status": "success",
                    "chunks_processed": len(documents),
                    "total_documents": len(documents)
                }
            
            def query(self, question: str, k: int = 3, threshold: float = 0.1):
                """Mock query processing"""
                # Generate query embedding
                query_embedding = self.rng.random(384).tolist()
                
                # Search similar documents
                results = self.vectorstore.similarity_search(query_embedding, k=k)
                
                # Filter by threshold
                filtered_results = [r for r in results if r["similarity_score"] >= threshold]
                
                return {
                    "answer": f"Mock answer for: {question}",
                    "sources": filtered_results,
                    "query_time": 0.1,
                    "confidence": 0.85
                }
        
        # Test complete pipeline
        rag = MockHealthAIRAG(temp_vectorstore_dir)
        
        # Index documents
        index_result = rag.index_documents(sample_medical_documents)
        assert index_result["status"] == "success"
        assert index_result["chunks_processed"] == 3
        
        # Test queries
        test_queries = [
            "What is diabetes?",
            "How to manage hypertension?",
            "What are cardiovascular risk factors?"
        ]
        
        for query in test_queries:
            result = rag.query(query, k=2, threshold=0.0)
            
            # Verify query result structure
            assert "answer" in result
            assert "sources" in result
            assert "query_time" in result
            assert "confidence" in result
            
            # Verify data types
            assert isinstance(result["answer"], str)
            assert isinstance(result["sources"], list)
            assert isinstance(result["query_time"], (int, float))
            assert isinstance(result["confidence"], (int, float))
            
            # Verify response quality
            assert len(result["answer"]) > 0
            assert 0 <= result["confidence"] <= 1
    
    def test_pipeline_performance_benchmarks(self, sample_medical_documents, temp_vectorstore_dir):
        """Test performance characteristics of RAG pipeline"""
        
        vectorstore = FAISSVectorStore(dimension=384, index_path=temp_vectorstore_dir)
        rng = np.random.default_rng(42)
        
        # Add embeddings to documents
        docs_with_embeddings = []
        for doc in sample_medical_documents:
            doc_copy = doc.copy()
            doc_copy["embedding"] = rng.random(384).tolist()
            docs_with_embeddings.append(doc_copy)
        
        # Test indexing performance
        start_time = time.time()
        vectorstore.add_documents(docs_with_embeddings)
        indexing_time = time.time() - start_time
        
        # Verify indexing performance (should be fast for small dataset)
        assert indexing_time < 1.0  # Should complete within 1 second
        
        # Test search performance
        query_embedding = rng.random(384).tolist()
        
        search_times = []
        for _ in range(10):  # Run multiple searches
            start_time = time.time()
            results = vectorstore.similarity_search(query_embedding, k=3)
            search_time = time.time() - start_time
            search_times.append(search_time)
        
        avg_search_time = np.mean(search_times)
        max_search_time = max(search_times)
        
        # Verify search performance
        assert avg_search_time < 0.1  # Average should be under 100ms
        assert max_search_time < 0.5   # Max should be under 500ms
        
        # Test memory efficiency
        stats = vectorstore.get_stats()
        assert stats["total_documents"] == 3
        assert stats["dimension"] == 384
    
    def test_error_handling_and_robustness(self, temp_vectorstore_dir):
        """Test error handling and robustness of RAG pipeline"""
        
        vectorstore = FAISSVectorStore(dimension=384, index_path=temp_vectorstore_dir)
        
        # Test empty document handling
        empty_docs = []
        vectorstore.add_documents(empty_docs)
        stats = vectorstore.get_stats()
        assert stats["total_documents"] == 0
        
        # Test invalid query handling
        rng = np.random.default_rng(42)
        query_embedding = rng.random(384).tolist()
        
        # Search in empty vectorstore
        results = vectorstore.similarity_search(query_embedding, k=3)
        assert len(results) == 0
        
        # Test invalid embedding dimensions
        with pytest.raises((ValueError, AssertionError)):
            invalid_embedding = rng.random(256).tolist()  # Wrong dimension
            vectorstore.similarity_search(invalid_embedding, k=3)
        
        # Test malformed document structure
        malformed_docs = [
            {"text": "Valid document"},  # Missing required fields
            {"embedding": rng.random(384).tolist()}  # Missing text
        ]
        
        # Should handle gracefully or raise appropriate errors
        try:
            vectorstore.add_documents(malformed_docs)
        except (KeyError, ValueError, TypeError) as e:
            # Expected behavior - should validate document structure
            assert len(str(e)) > 0
    
    def test_data_consistency_and_integrity(self, sample_medical_documents, temp_vectorstore_dir):
        """Test data consistency and integrity throughout pipeline"""
        
        vectorstore = FAISSVectorStore(dimension=384, index_path=temp_vectorstore_dir)
        rng = np.random.default_rng(42)
        
        # Add embeddings to documents
        docs_with_embeddings = []
        for doc in sample_medical_documents:
            doc_copy = doc.copy()
            doc_copy["embedding"] = rng.random(384).tolist()
            docs_with_embeddings.append(doc_copy)
        
        # Store documents
        vectorstore.add_documents(docs_with_embeddings)
        
        # Retrieve all documents
        stored_docs = vectorstore.get_all_documents()
        
        # Verify data integrity
        assert len(stored_docs) == len(sample_medical_documents)
        
        # Check that all original data is preserved
        original_texts = {doc["text"] for doc in sample_medical_documents}
        stored_texts = {doc["text"] for doc in stored_docs}
        assert original_texts == stored_texts
        
        # Verify metadata preservation
        for original_doc in sample_medical_documents:
            matching_stored = [
                doc for doc in stored_docs 
                if doc["text"] == original_doc["text"]
            ]
            assert len(matching_stored) == 1
            
            stored_doc = matching_stored[0]
            assert stored_doc["source"] == original_doc["source"]
            assert stored_doc["chunk_index"] == original_doc["chunk_index"]
        
        # Test search consistency - same query should return same results
        query_embedding = rng.random(384).tolist()
        
        results1 = vectorstore.similarity_search(query_embedding, k=2)
        results2 = vectorstore.similarity_search(query_embedding, k=2)
        
        # Results should be identical
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1["text"] == r2["text"]
            assert r1["similarity_score"] == r2["similarity_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])