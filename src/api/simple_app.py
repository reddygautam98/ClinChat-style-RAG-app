from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HealthAI RAG - Demo")

class Query(BaseModel):
    question: str
    use_fusion: bool = True
    model_preference: str = "auto"  # auto, gemini, groq

class Answer(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    model_used: str
    confidence_score: float

@app.post("/query", response_model=Answer)
async def query(q: Query):
    """Main query endpoint - placeholder implementation"""
    try:
        # Placeholder response until AI models are properly configured
        response_text = f"Received your question: {q.question}. This is a placeholder response. The AI models (Gemini & Groq) are configured but need proper environment setup."
        
        return Answer(
            answer=response_text,
            sources=[],
            model_used="placeholder",
            confidence_score=0.9
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "HealthAI RAG server is running",
        "ai_models": {
            "gemini": "configured_but_not_loaded",
            "groq": "configured_but_not_loaded"
        },
        "fusion_ai_enabled": False
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HealthAI RAG - Medical AI Assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "Server is running - AI models will be loaded when environment is properly configured"
    }