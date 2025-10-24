"""
Refactored End-to-End test for HealthAI RAG Application
Reduced cognitive complexity by breaking down the monolithic test function
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from src.rag.retrieval_chain import HealthAIRAG


class RAGTestSuite:
    """Refactored E2E test suite with reduced cognitive complexity"""
    
    def __init__(self, vectorstore_path: str = "data/vectorstore"):
        """Initialize the test suite with RAG system"""
        self.vectorstore_path = vectorstore_path
        self.rag = None
        self.test_results = {}
        
    def initialize_rag_system(self) -> bool:
        """Initialize the RAG system - Complexity: 3"""
        print("1. Initializing RAG system...")
        try:
            self.rag = HealthAIRAG(vectorstore_path=self.vectorstore_path)
            print("   ✅ RAG system initialized")
            return True
        except Exception as e:
            print(f"   ❌ Failed to initialize RAG system: {e}")
            return False
    
    def verify_pdf_availability(self, pdf_directory: str = "data/pdfs") -> bool:
        """Verify PDF files are available for testing - Complexity: 4"""
        print("2. Checking PDF availability...")
        
        if not Path(pdf_directory).exists():
            print(f"   ❌ PDF directory not found: {pdf_directory}")
            print("   Run 'python create_test_pdfs.py' first to create test PDFs")
            return False
        
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        if not pdf_files:
            print(f"   ❌ No PDF files found in {pdf_directory}")
            return False
        
        print(f"   📄 Found {len(pdf_files)} PDF files:")
        for pdf in pdf_files:
            print(f"      - {pdf.name}")
        
        return True
    
    def index_documents(self, pdf_directory: str = "data/pdfs") -> bool:
        """Index PDF documents and measure performance - Complexity: 5"""
        print("3. Indexing PDF documents...")
        
        start_time = time.time()
        indexing_result = self.rag.index_documents(pdf_directory)
        indexing_time = time.time() - start_time
        
        print(f"   ⏱️  Indexing completed in {indexing_time:.2f} seconds")
        
        if indexing_result["status"] == "success":
            print(f"   ✅ Successfully indexed {indexing_result['chunks_processed']} chunks")
            print(f"   📊 Total documents in vector store: {indexing_result['total_documents']}")
            self.test_results["indexing"] = {
                "success": True,
                "chunks_processed": indexing_result["chunks_processed"],
                "total_documents": indexing_result["total_documents"],
                "indexing_time": indexing_time
            }
            return True
        else:
            print(f"   ❌ Indexing failed: {indexing_result['message']}")
            self.test_results["indexing"] = {"success": False, "error": indexing_result["message"]}
            return False
    
    def get_test_queries(self) -> List[Dict[str, Any]]:
        """Get predefined test queries - Complexity: 1"""
        return [
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
    
    def execute_single_query(self, query_test: Dict[str, Any], query_index: int) -> Dict[str, Any]:
        """Execute a single query and return results - Complexity: 6"""
        question = query_test['question']
        expected_topics = query_test['expected_topics']
        
        print(f"\n   Query {query_index}: {question}")
        
        start_time = time.time()
        result = self.rag.query(question, k=3, threshold=0.1)
        query_time = time.time() - start_time
        
        print(f"   ⏱️  Response time: {query_time:.2f} seconds")
        
        query_result = {
            "question": question,
            "query_time": query_time,
            "success": False,
            "has_answer": False,
            "has_sources": False,
            "topic_match": False
        }
        
        if result and "answer" in result:
            query_result["has_answer"] = True
            print(f"   💡 Answer: {result['answer'][:100]}...")
            
            if "sources" in result and result["sources"]:
                query_result["has_sources"] = True
                print(f"   📚 Sources found: {len(result['sources'])}")
                
                # Check topic relevance
                answer_lower = result['answer'].lower()
                topic_found = any(topic.lower() in answer_lower for topic in expected_topics)
                query_result["topic_match"] = topic_found
                
                if topic_found:
                    print("   ✅ Query successful - relevant answer found")
                    query_result["success"] = True
                else:
                    print("   ⚠️  Answer may not be fully relevant to expected topics")
            else:
                print("   ⚠️  No sources found")
        else:
            print("   ❌ No answer generated")
        
        return query_result
    
    def execute_all_queries(self) -> Dict[str, Any]:
        """Execute all test queries and collect results - Complexity: 5"""
        print("4. Testing RAG queries...")
        
        test_queries = self.get_test_queries()
        successful_queries = 0
        total_response_time = 0
        query_results = []
        
        for i, query_test in enumerate(test_queries, 1):
            query_result = self.execute_single_query(query_test, i)
            query_results.append(query_result)
            
            if query_result["success"]:
                successful_queries += 1
            
            total_response_time += query_result["query_time"]
        
        avg_response_time = total_response_time / len(test_queries)
        
        return {
            "total_queries": len(test_queries),
            "successful_queries": successful_queries,
            "success_rate": successful_queries / len(test_queries),
            "avg_response_time": avg_response_time,
            "total_response_time": total_response_time,
            "query_results": query_results
        }
    
    def analyze_performance(self, query_metrics: Dict[str, Any]) -> None:
        """Analyze and display performance metrics - Complexity: 4"""
        print("5. Performance Analysis")
        print(f"   📊 Success rate: {query_metrics['success_rate']:.1%}")
        print(f"   ⏱️  Average response time: {query_metrics['avg_response_time']:.2f} seconds")
        print(f"   🔍 Successful queries: {query_metrics['successful_queries']}/{query_metrics['total_queries']}")
        
        if query_metrics['avg_response_time'] < 2.0:
            print("   ✅ Response time performance: Excellent")
        elif query_metrics['avg_response_time'] < 5.0:
            print("   ⚠️  Response time performance: Acceptable")
        else:
            print("   ❌ Response time performance: Needs improvement")
    
    def collect_system_statistics(self) -> Dict[str, Any]:
        """Collect system statistics and configuration - Complexity: 3"""
        print("6. System Statistics")
        
        stats = {}
        
        # Vector store statistics
        if hasattr(self.rag, 'vector_store') and hasattr(self.rag.vector_store, 'get_stats'):
            vector_stats = self.rag.vector_store.get_stats()
            stats["vector_store"] = vector_stats
            print("   📚 Vector Store:")
            print(f"      - Total documents: {vector_stats.get('total_documents', 'N/A')}")
            print(f"      - Index dimension: {vector_stats.get('dimension', 'N/A')}")
        else:
            print("   📚 Vector Store: Statistics unavailable")
            stats["vector_store"] = None
        
        # AI service configuration
        ai_services = []
        if hasattr(self.rag, 'gemini_client') and self.rag.gemini_client:
            ai_services.append("Google Gemini")
        if hasattr(self.rag, 'groq_client') and self.rag.groq_client:
            ai_services.append("Groq")
        
        stats["ai_services"] = ai_services
        print("   🤖 AI Services:")
        if ai_services:
            for service in ai_services:
                print(f"      - {service}: Available")
        else:
            print("      - No AI services configured")
        
        return stats
    
    def generate_final_report(self, query_metrics: Dict[str, Any], system_stats: Dict[str, Any]) -> bool:
        """Generate final test report and recommendations - Complexity: 8"""
        print("\n🎯 Final Test Report:")
        
        overall_success = True
        
        # Check indexing results
        if self.test_results.get("indexing", {}).get("success", False):
            print("   ✅ Document indexing: PASSED")
        else:
            print("   ❌ Document indexing: FAILED")
            overall_success = False
        
        # Check query performance
        if query_metrics["success_rate"] >= 0.8:  # 80% success rate threshold
            print("   ✅ Query processing: PASSED")
        else:
            print("   ❌ Query processing: FAILED (below 80% success rate)")
            overall_success = False
        
        # Check response times
        if query_metrics["avg_response_time"] <= 5.0:  # 5 second threshold
            print("   ✅ Response time: PASSED")
        else:
            print("   ❌ Response time: FAILED (exceeds 5 second threshold)")
            overall_success = False
        
        # Check system components
        vector_store_ok = system_stats.get("vector_store") is not None
        ai_services_ok = len(system_stats.get("ai_services", [])) > 0
        
        if vector_store_ok and ai_services_ok:
            print("   ✅ System components: PASSED")
        else:
            print("   ❌ System components: FAILED")
            if not vector_store_ok:
                print("      - Vector store not properly configured")
            if not ai_services_ok:
                print("      - No AI services available")
            overall_success = False
        
        # Generate recommendations
        self.generate_recommendations(query_metrics, system_stats, overall_success)
        
        return overall_success
    
    def generate_recommendations(self, query_metrics: Dict[str, Any], 
                               system_stats: Dict[str, Any], overall_success: bool) -> None:
        """Generate recommendations based on test results - Complexity: 6"""
        print("\n💡 Recommendations:")
        
        if overall_success:
            print("   🎉 All tests passed! System is ready for production.")
            print("   📊 Vector store and retrieval working correctly")
            print("   🔍 Document indexing and search functional")
        else:
            print("   ⚠️  Some issues detected. Please address the following:")
            
            # AI service recommendations
            ai_services = system_stats.get("ai_services", [])
            if "Google Gemini" not in ai_services:
                print("   - Check Google Gemini API key configuration")
            if "Groq" not in ai_services:
                print("   - Check Groq API key configuration and model availability")
            if not ai_services:
                print("   - Verify API keys are set in .env file")
                print("   - Check internet connection for API calls")
        
        print("\n🎉 End-to-end test completed!")


def run_e2e_test():
    """Main entry point for E2E testing - Complexity: 2"""
    print("🚀 Starting End-to-End HealthAI RAG Test")
    print("=" * 60)
    
    test_suite = RAGTestSuite()
    
    # Execute test steps
    if not test_suite.initialize_rag_system():
        return False
    
    if not test_suite.verify_pdf_availability():
        return False
    
    if not test_suite.index_documents():
        return False
    
    query_metrics = test_suite.execute_all_queries()
    test_suite.analyze_performance(query_metrics)
    
    system_stats = test_suite.collect_system_statistics()
    
    return test_suite.generate_final_report(query_metrics, system_stats)


if __name__ == "__main__":
    success = run_e2e_test()
    exit(0 if success else 1)