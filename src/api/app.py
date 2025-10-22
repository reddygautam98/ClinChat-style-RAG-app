from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq
import asyncio
from typing import List, Dict, Any
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ClinChat RAG - Demo")

class Query(BaseModel):
    question: str
    use_fusion: bool = True
    model_preference: str = "auto"  # auto, gemini, groq

class Answer(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    model_used: str
    confidence_score: float

# Initialize AI clients
gemini_client = None
groq_client = None

def initialize_ai_clients():
    """Initialize Gemini and Groq clients"""
    global gemini_client, groq_client
    
    try:
        # Initialize Gemini
        gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            gemini_client = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini client initialized successfully")
        
        # Initialize Groq
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            groq_client = Groq(api_key=groq_api_key)
            logger.info("Groq client initialized successfully")
            
    except Exception as e:
        logger.error(f"Error initializing AI clients: {e}")

# Initialize clients on startup
initialize_ai_clients()

async def get_gemini_response(question: str) -> Dict[str, Any]:
    """Get response from Google Gemini"""
    try:
        if not gemini_client:
            raise ValueError("Gemini client not initialized")
        
        prompt = f"""You are a clinical AI assistant. Please provide accurate, helpful medical information.
        
Question: {question}

Please provide a comprehensive answer based on medical knowledge."""
        
        response = gemini_client.generate_content(prompt)
        
        return {
            "answer": response.text,
            "model": "gemini-pro",
            "confidence": 0.85  # Simplified confidence scoring
        }
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return {
            "answer": f"Gemini error: {str(e)}",
            "model": "gemini-pro",
            "confidence": 0.0
        }

async def get_groq_response(question: str) -> Dict[str, Any]:
    """Get response from Groq"""
    try:
        if not groq_client:
            raise ValueError("Groq client not initialized")
        
        messages = [
            {"role": "system", "content": "You are a clinical AI assistant. Provide accurate, helpful medical information based on established medical knowledge."},
            {"role": "user", "content": question}
        ]
        
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
        
        return {
            "answer": response.choices[0].message.content,
            "model": "mixtral-8x7b-32768",
            "confidence": 0.80  # Simplified confidence scoring
        }
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return {
            "answer": f"Groq error: {str(e)}",
            "model": "mixtral-8x7b-32768",
            "confidence": 0.0
        }

async def fusion_ai_response(question: str) -> Dict[str, Any]:
    """Get fusion response from both models"""
    try:
        # Get responses from both models concurrently
        tasks = []
        if gemini_client:
            tasks.append(get_gemini_response(question))
        if groq_client:
            tasks.append(get_groq_response(question))
        
        if not tasks:
            raise ValueError("No AI models available")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, dict) and r.get("confidence", 0) > 0]
        
        if not valid_results:
            raise ValueError("All models failed to respond")
        
        # Simple fusion strategy: use highest confidence
        best_result = max(valid_results, key=lambda x: x["confidence"])
        
        return {
            "answer": best_result["answer"],
            "model": f"fusion-ai ({best_result['model']})",
            "confidence": best_result["confidence"],
            "all_responses": valid_results
        }
        
    except Exception as e:
        logger.error(f"Fusion AI error: {e}")
        return {
            "answer": f"Fusion AI error: {str(e)}",
            "model": "fusion-ai",
            "confidence": 0.0
        }

@app.post("/query", response_model=Answer)
async def query(q: Query):
    """Main query endpoint with AI model selection"""
    try:
        if q.model_preference == "gemini" and gemini_client:
            result = await get_gemini_response(q.question)
        elif q.model_preference == "groq" and groq_client:
            result = await get_groq_response(q.question)
        elif q.use_fusion:
            result = await fusion_ai_response(q.question)
        else:
            # Default fallback
            if gemini_client:
                result = await get_gemini_response(q.question)
            elif groq_client:
                result = await get_groq_response(q.question)
            else:
                raise HTTPException(status_code=503, detail="No AI models available")
        
        return Answer(
            answer=result["answer"],
            sources=[],  # TODO: Implement RAG sources
            model_used=result["model"],
            confidence_score=result["confidence"]
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    models_status = {}
    
    # Check Gemini status
    if gemini_client:
        try:
            test_response = await get_gemini_response("Hello")
            models_status["gemini"] = "healthy" if test_response["confidence"] > 0 else "error"
        except:
            models_status["gemini"] = "error"
    else:
        models_status["gemini"] = "not_configured"
    
    # Check Groq status
    if groq_client:
        try:
            test_response = await get_groq_response("Hello")
            models_status["groq"] = "healthy" if test_response["confidence"] > 0 else "error"
        except:
            models_status["groq"] = "error"
    else:
        models_status["groq"] = "not_configured"
    
    return {
        "status": "ok",
        "models": models_status,
        "fusion_ai_enabled": bool(gemini_client and groq_client)
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ClinChat RAG - Medical AI Assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }