import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to" in response.json()["message"]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_endpoint():
    response = client.post(
        "/api/v1/chat/",
        json={"message": "What is diabetes?", "use_rag": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["conversation_id"] == "default"


def test_list_documents():
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)