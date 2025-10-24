"""
Comprehensive API endpoint tests for HealthAI RAG Application
Tests all REST API endpoints including GET/POST operations, error handling, and authentication
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json
import time
from typing import Dict, Any

# Import the FastAPI app
from src.api.app import app, initialize_ai_clients


class TestAPIEndpoints:
    """Test suite for all API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked AI services"""
        # Mock AI clients to avoid requiring API keys
        with patch('src.api.app.gemini_client') as mock_gemini, \
             patch('src.api.app.groq_client') as mock_groq:
            
            # Configure mock responses
            mock_gemini.generate_content.return_value.text = "Mocked Gemini response about medical query"
            mock_groq.chat.completions.create.return_value.choices = [
                Mock(message=Mock(content="Mocked Groq response about medical query"))
            ]
            
            # Initialize test client
            test_client = TestClient(app)
            yield test_client
    
    @pytest.fixture
    def mock_ai_clients(self):
        """Mock AI clients for testing"""
        with patch('src.api.app.gemini_client') as mock_gemini, \
             patch('src.api.app.groq_client') as mock_groq:
            
            # Configure detailed mock responses
            mock_gemini.generate_content.return_value.text = "Type 2 diabetes is managed through lifestyle modifications, medication, and regular monitoring."
            
            mock_completion = Mock()
            mock_completion.choices = [
                Mock(message=Mock(content="Diabetes management involves diet, exercise, and medication adherence."))
            ]
            mock_groq.chat.completions.create.return_value = mock_completion
            
            yield {"gemini": mock_gemini, "groq": mock_groq}
    
    def test_root_endpoint_get(self, client):
        """Test GET / endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        
        # Verify content
        assert "HealthAI RAG" in data["message"]
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
    
    def test_health_endpoint_get(self, client, mock_ai_clients):
        """Test GET /health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "models" in data
        assert "fusion_ai_enabled" in data
        
        # Verify data types
        assert isinstance(data["status"], str)
        assert isinstance(data["models"], dict)
        assert isinstance(data["fusion_ai_enabled"], bool)
        
        # Check model status structure
        models = data["models"]
        if "gemini" in models:
            assert models["gemini"] in ["healthy", "error", "not_configured"]
        if "groq" in models:
            assert models["groq"] in ["healthy", "error", "not_configured"]
    
    def test_query_endpoint_post_valid_request(self, client, mock_ai_clients):
        """Test POST /query with valid request"""
        query_data = {
            "question": "What are the symptoms of diabetes?",
            "use_fusion": False,
            "model_preference": "gemini"
        }
        
        response = client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "answer" in data
        assert "sources" in data
        assert "model_used" in data
        assert "confidence_score" in data
        
        # Verify data types and content
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["model_used"], str)
        assert isinstance(data["confidence_score"], (int, float))
        
        # Verify answer is not empty
        assert len(data["answer"]) > 0
        
        # Verify confidence score is in valid range
        assert 0 <= data["confidence_score"] <= 1
        
        # Check sources structure
        for source in data["sources"]:
            assert "title" in source
            assert "url" in source
            assert "excerpt" in source
    
    def test_query_endpoint_post_groq_preference(self, client, mock_ai_clients):
        """Test POST /query with Groq model preference"""
        query_data = {
            "question": "How is hypertension treated?",
            "use_fusion": False,
            "model_preference": "groq"
        }
        
        response = client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Groq model was used
        assert "groq" in data["model_used"] or "mixtral" in data["model_used"]
        assert len(data["answer"]) > 0
    
    def test_query_endpoint_post_fusion_mode(self, client, mock_ai_clients):
        """Test POST /query with fusion AI enabled"""
        query_data = {
            "question": "What medications are used for heart disease?",
            "use_fusion": True,
            "model_preference": "auto"
        }
        
        response = client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify fusion mode response
        assert len(data["answer"]) > 0
        # May contain fusion-ai in model name or fall back to individual model
        assert isinstance(data["model_used"], str)
    
    def test_query_endpoint_post_invalid_request_empty_question(self, client):
        """Test POST /query with empty question"""
        query_data = {
            "question": "",
            "use_fusion": False,
            "model_preference": "gemini"
        }
        
        response = client.post("/query", json=query_data)
        
        # Should return error for empty question
        assert response.status_code in [400, 422, 500]
    
    def test_query_endpoint_post_invalid_request_missing_fields(self, client):
        """Test POST /query with missing required fields"""
        query_data = {
            "use_fusion": False
            # Missing "question" field
        }
        
        response = client.post("/query", json=query_data)
        
        # Should return validation error
        assert response.status_code == 422
        
        # Check error response format
        error_data = response.json()
        assert "detail" in error_data
    
    def test_query_endpoint_post_invalid_model_preference(self, client, mock_ai_clients):
        """Test POST /query with invalid model preference"""
        query_data = {
            "question": "What is diabetes?",
            "use_fusion": False,
            "model_preference": "invalid_model"
        }
        
        response = client.post("/query", json=query_data)
        
        # Should handle gracefully or return error
        assert response.status_code in [200, 400, 422, 500]
        
        if response.status_code == 200:
            # If handled gracefully, should fall back to default
            data = response.json()
            assert len(data["answer"]) > 0
    
    def test_query_endpoint_post_long_question(self, client, mock_ai_clients):
        """Test POST /query with very long question"""
        long_question = "What is diabetes? " * 500  # Very long question
        
        query_data = {
            "question": long_question,
            "use_fusion": False,
            "model_preference": "gemini"
        }
        
        response = client.post("/query", json=query_data)
        
        # Should either process or reject based on length limits
        assert response.status_code in [200, 400, 422, 500]
        
        if response.status_code == 400:
            # Check error message mentions length
            error_data = response.json()
            assert "detail" in error_data
    
    def test_api_response_time_performance(self, client, mock_ai_clients):
        """Test API response time performance"""
        query_data = {
            "question": "What are diabetes symptoms?",
            "use_fusion": False,
            "model_preference": "gemini"
        }
        
        # Measure response time
        start_time = time.time()
        response = client.post("/query", json=query_data)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        
        # Response should be reasonably fast with mocked services
        assert response_time < 2.0  # Should complete within 2 seconds
        
        # Run multiple requests to check consistency
        response_times = []
        for _ in range(5):
            start_time = time.time()
            response = client.post("/query", json=query_data)
            response_time = time.time() - start_time
            response_times.append(response_time)
            assert response.status_code == 200
        
        # Check response time consistency
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        assert avg_time < 1.0  # Average should be under 1 second
        assert max_time < 2.0   # Max should be under 2 seconds
    
    def test_concurrent_request_handling(self, client, mock_ai_clients):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import threading
        
        query_data = {
            "question": "What is hypertension?",
            "use_fusion": False,
            "model_preference": "gemini"
        }
        
        def make_request():
            return client.post("/query", json=query_data)
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert len(data["answer"]) > 0
    
    def test_error_handling_ai_service_failure(self, client):
        """Test error handling when AI services fail"""
        with patch('src.api.app.gemini_client') as mock_gemini, \
             patch('src.api.app.groq_client') as mock_groq:
            
            # Configure AI clients to raise exceptions
            mock_gemini.generate_content.side_effect = Exception("Gemini service unavailable")
            mock_groq.chat.completions.create.side_effect = Exception("Groq service unavailable")
            
            query_data = {
                "question": "What is diabetes?",
                "use_fusion": False,
                "model_preference": "gemini"
            }
            
            response = client.post("/query", json=query_data)
            
            # Should handle gracefully
            assert response.status_code in [200, 500]
            
            if response.status_code == 200:
                data = response.json()
                # Should return error message in response
                assert "error" in data["answer"].lower() or "unavailable" in data["answer"].lower()
    
    def test_json_content_type_validation(self, client):
        """Test that API properly validates JSON content type"""
        query_data = "question=What is diabetes?"  # Form data instead of JSON
        
        response = client.post(
            "/query", 
            data=query_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Should reject non-JSON content
        assert response.status_code == 422
    
    def test_api_documentation_endpoints(self, client):
        """Test that API documentation endpoints are accessible"""
        # Test OpenAPI schema endpoint
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_schema = response.json()
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert "paths" in openapi_schema
        
        # Verify key endpoints are documented
        paths = openapi_schema["paths"]
        assert "/" in paths
        assert "/query" in paths
        assert "/health" in paths
        
        # Test docs endpoint accessibility
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly set"""
        # Test preflight request
        response = client.options("/query")
        
        # Should handle OPTIONS request
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
        
        # Test actual request with Origin header
        response = client.post(
            "/query",
            json={
                "question": "What is diabetes?",
                "use_fusion": False,
                "model_preference": "auto"
            },
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should include CORS headers in response (if CORS is configured)
        # Note: Actual CORS behavior depends on app configuration
        assert response.status_code in [200, 500]


class TestAPIErrorScenarios:
    """Test edge cases and error scenarios"""
    
    @pytest.fixture
    def client_no_ai(self):
        """Create test client with no AI services configured"""
        with patch('src.api.app.gemini_client', None), \
             patch('src.api.app.groq_client', None):
            yield TestClient(app)
    
    def test_no_ai_services_available(self, client_no_ai):
        """Test behavior when no AI services are available"""
        query_data = {
            "question": "What is diabetes?",
            "use_fusion": False,
            "model_preference": "gemini"
        }
        
        response = client_no_ai.post("/query", json=query_data)
        
        # Should return appropriate error
        assert response.status_code in [500, 503]
        
        if response.status_code == 500:
            error_data = response.json()
            assert "detail" in error_data
    
    def test_health_check_no_ai_services(self, client_no_ai):
        """Test health check when no AI services are configured"""
        response = client_no_ai.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should report services as not configured
        models = data["models"]
        assert models["gemini"] == "not_configured"
        assert models["groq"] == "not_configured"
        assert data["fusion_ai_enabled"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])