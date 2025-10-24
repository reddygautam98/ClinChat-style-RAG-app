"""
Pytest configuration and fixtures for HealthAI RAG tests
"""

import sys
import os
from pathlib import Path

# Add the project root and src directories to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from fastapi.testclient import TestClient
import tempfile
import shutil


@pytest.fixture(scope="session")
def temp_data_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session") 
def test_client():
    """Create a test client for the FastAPI app"""
    from src.main import app
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_embeddings():
    """Mock embeddings for testing"""
    import numpy as np
    rng = np.random.default_rng(42)  # Secure seeded generator for reproducible tests
    return {
        "test_doc_1": rng.random(384),
        "test_doc_2": rng.random(384),
        "test_doc_3": rng.random(384)
    }


@pytest.fixture(scope="function")
def sample_medical_query():
    """Sample medical query for testing"""
    return "What are the symptoms of type 2 diabetes?"


@pytest.fixture(scope="function")
def sample_documents():
    """Sample medical documents for testing"""
    return [
        {
            "id": "doc_1",
            "content": "Type 2 diabetes symptoms include increased thirst, frequent urination, fatigue, and blurred vision.",
            "metadata": {"source": "medical_guidelines", "category": "diabetes"}
        },
        {
            "id": "doc_2", 
            "content": "Common signs of diabetes are excessive hunger, unexplained weight loss, and slow healing wounds.",
            "metadata": {"source": "clinical_manual", "category": "symptoms"}
        },
        {
            "id": "doc_3",
            "content": "Hypertension treatment includes lifestyle changes and medications like ACE inhibitors.",
            "metadata": {"source": "treatment_guidelines", "category": "hypertension"}
        }
    ]


@pytest.fixture(scope="function")
def mock_ai_response():
    """Mock AI model response for testing"""
    return {
        "answer": "Type 2 diabetes symptoms include increased thirst (polydipsia), frequent urination (polyuria), fatigue, blurred vision, and unexplained weight loss.",
        "confidence": 0.92,
        "model_used": "gemini",
        "processing_time": 1.23,
        "sources": ["doc_1", "doc_2"],
        "fusion_strategy": "weighted_average"
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, temp_data_dir):
    """Setup test environment variables"""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATA_PATH", temp_data_dir)
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    # Mock API keys for testing
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_key")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")