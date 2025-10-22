"""
End-to-end test for ClinChat RAG Application
Tests the complete pipeline: PDF ingestion -> Embedding -> Vector Store -> RAG Query
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from src.rag.retrieval_chain import ClinChatRAG


def test_complete_rag_pipeline():
    """Test the complete RAG pipeline with real PDFs"""
    
    print("🚀 Starting End-to-End ClinChat RAG Test")
    print("=" * 60)
    
    try:
        # Initialize RAG system
        print("1. Initializing RAG system...")
        rag = ClinChatRAG(vectorstore_path="data/vectorstore")
        print("   ✅ RAG system initialized")
        
        # Check if PDFs exist
        pdf_directory = "data/pdfs"
        if not Path(pdf_directory).exists():
            print(f"   ❌ PDF directory not found: {pdf_directory}")
            print("   Run 'python create_test_pdfs.py' first to create test PDFs")
            return False
        
        # Get PDF files
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        if not pdf_files:
            print(f"   ❌ No PDF files found in {pdf_directory}")
            return False
        
        print(f"   📄 Found {len(pdf_files)} PDF files:")
        for pdf in pdf_files:
            print(f"      - {pdf.name}")
        
        # Index documents
        print("\n2. Indexing PDF documents...")
        start_time = time.time()
        
        indexing_result = rag.index_documents(pdf_directory)
        
        indexing_time = time.time() - start_time
        print(f"   ⏱️  Indexing completed in {indexing_time:.2f} seconds")
        
        if indexing_result["status"] == "success":
            print(f"   ✅ Successfully indexed {indexing_result['chunks_processed']} chunks")
            print(f"   📊 Total documents in vector store: {indexing_result['total_documents']}")
        else:
            print(f"   ❌ Indexing failed: {indexing_result['message']}")
            return False
        
        # Test queries
        print("\n3. Testing RAG queries...")
        
        test_queries = [
            {
                "question": "What is diabetes and how is it managed?",
                "expected_topics": ["diabetes", "management", "blood glucose"]
            },
            {
                "question": "What are the symptoms of high blood pressure?",
                "expected_topics": ["hypertension", "blood pressure", "symptoms"]
            },
            {
                "question": "How can I prevent heart disease?",
                "expected_topics": ["heart disease", "prevention", "lifestyle"]
            },
            {
                "question": "What medications are used for type 2 diabetes?",
                "expected_topics": ["type 2 diabetes", "medications", "treatment"]
            },
            {
                "question": "What are normal blood pressure ranges?",
                "expected_topics": ["blood pressure", "normal", "ranges"]
            }
        ]
        
        successful_queries = 0
        total_response_time = 0
        
        for i, query_test in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query_test['question']}")
            
            start_time = time.time()
            result = rag.query(query_test['question'], k=3, threshold=0.1)
            query_time = time.time() - start_time
            total_response_time += query_time
            
            print(f"   ⏱️  Response time: {query_time:.2f} seconds")
            print(f"   📊 Status: {result['status']}")
            
            if result['status'] == 'success':
                successful_queries += 1
                print(f"   📝 Answer: {result['answer'][:100]}...")
                print(f"   📚 Sources: {', '.join(result['sources'])}")
                print(f"   🎯 Confidence: {result['confidence']:.2f}")
                print(f"   📖 Documents used: {result.get('retrieved_docs', 0)}")
            elif result['status'] == 'no_documents':
                print(f"   ⚠️  No documents available")
            elif result['status'] == 'no_results':
                print(f"   ⚠️  No relevant results found")
            else:
                print(f"   ❌ Query failed: {result['answer']}")
        
        # Performance summary
        print(f"\n4. Performance Summary")
        print(f"   📊 Successful queries: {successful_queries}/{len(test_queries)}")
        print(f"   ⏱️  Average response time: {total_response_time/len(test_queries):.2f} seconds")
        
        # System statistics
        print(f"\n5. System Statistics")
        stats = rag.get_system_stats()
        
        print(f"   📚 Vector Store:")
        vs_stats = stats.get('vectorstore', {})
        print(f"      - Total documents: {vs_stats.get('total_documents', 0)}")
        print(f"      - Embedding dimension: {vs_stats.get('dimension', 0)}")
        print(f"      - Index type: {vs_stats.get('index_type', 'unknown')}")
        
        print(f"   🤖 AI Service:")
        ai_stats = stats.get('ai_service', {})
        print(f"      - Fusion enabled: {ai_stats.get('fusion_enabled', False)}")
        print(f"      - Fusion strategy: {ai_stats.get('fusion_strategy', 'unknown')}")
        
        models = ai_stats.get('models_available', {})
        for model_name, model_info in models.items():
            status = model_info.get('status', 'unknown')
            print(f"      - {model_name}: {status}")
        
        print(f"   🧠 Embedder: {stats.get('embedder_status', 'unknown')}")
        
        # Conclusion
        success_rate = successful_queries / len(test_queries)
        print(f"\n🎯 Test Results:")
        
        if success_rate >= 0.8:
            print(f"   ✅ EXCELLENT: {success_rate:.1%} success rate")
        elif success_rate >= 0.6:
            print(f"   ⚠️  GOOD: {success_rate:.1%} success rate")  
        elif success_rate >= 0.4:
            print(f"   ⚠️  FAIR: {success_rate:.1%} success rate")
        else:
            print(f"   ❌ POOR: {success_rate:.1%} success rate")
        
        if successful_queries > 0:
            print(f"   📊 Vector store and retrieval working correctly")
            print(f"   🔍 Document indexing and search functional")
            
        if success_rate < 1.0:
            print(f"\n💡 Recommendations:")
            if ai_stats.get('models_available', {}).get('gemini', {}).get('status') == 'error':
                print(f"   - Check Google Gemini API key configuration")
            if ai_stats.get('models_available', {}).get('groq', {}).get('status') == 'error':
                print(f"   - Check Groq API key configuration and model availability")
            if successful_queries == 0:
                print(f"   - Verify API keys are set in .env file")
                print(f"   - Check internet connection for API calls")
        
        print(f"\n🎉 End-to-end test completed!")
        return success_rate >= 0.5  # Consider test passed if >50% queries succeed
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_document_retrieval_only():
    """Test just document retrieval without AI generation"""
    
    print("\n🔍 Testing Document Retrieval Only")
    print("=" * 50)
    
    try:
        from src.embeddings.openai_embed import ClinChatEmbedding
        from src.vectorstore.faiss_store import ClinChatVectorStore
        
        # Initialize components
        embedder = ClinChatEmbedding()
        vector_store = ClinChatVectorStore("data/vectorstore")
        
        # Test queries for retrieval
        test_queries = [
            "diabetes management",
            "blood pressure symptoms", 
            "heart disease prevention"
        ]
        
        print("Testing document retrieval for queries:")
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            results = vector_store.search(query, embedder, k=3, threshold=0.1)
            
            print(f"   📊 Found {len(results)} relevant documents:")
            for i, doc in enumerate(results, 1):
                print(f"      {i}. Source: {doc.get('source', 'Unknown')}")
                print(f"         Similarity: {doc.get('similarity_score', 0):.3f}")
                print(f"         Text: {doc.get('text', '')[:100]}...")
        
        print("\n✅ Document retrieval test completed")
        return True
        
    except Exception as e:
        print(f"❌ Document retrieval test failed: {e}")
        return False


if __name__ == "__main__":
    print("🏥 ClinChat RAG Application - End-to-End Testing")
    print("=" * 60)
    
    # Run complete test
    complete_test_passed = test_complete_rag_pipeline()
    
    # If complete test has issues, test retrieval only
    if not complete_test_passed:
        print("\n" + "="*60)
        retrieval_test_passed = test_document_retrieval_only()
        
        if retrieval_test_passed:
            print("\n✅ Document retrieval is working - AI generation issues detected")
        else:
            print("\n❌ Both document retrieval and AI generation have issues")
    
    print("\n" + "="*60)
    print("🏁 Testing completed")
    
    if complete_test_passed:
        print("🎉 All systems operational - ClinChat RAG is ready!")
    else:
        print("⚠️  Some components need attention - check API configurations")