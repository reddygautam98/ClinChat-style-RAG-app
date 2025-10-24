from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq
from typing import List, Dict, Any
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HealthAI RAG - Demo")

class Query(BaseModel):
    question: str
    use_fusion: bool = True
    model_preference: str = "auto"  # auto, gemini, groq
    
    def validate_question(self):
        """Validate and sanitize the question input"""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        
        # Check length limits
        if len(self.question) > 2000:
            raise ValueError("Question too long (max 2000 characters)")
        
        # Check for valid model preference
        valid_models = ["auto", "gemini", "groq"]
        if self.model_preference not in valid_models:
            raise ValueError(f"Invalid model preference. Must be one of: {valid_models}")
        
        return True

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

def get_gemini_response(question: str) -> Dict[str, Any]:
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
    except (ValueError, AttributeError) as e:
        logger.error(f"Gemini client error: {e}")
        return {
            "answer": f"Gemini client error: {str(e)}",
            "model": "gemini-pro",
            "confidence": 0.0
        }
    except Exception as e:
        logger.error(f"Unexpected Gemini error: {e}")
        return {
            "answer": "Service temporarily unavailable",
            "model": "gemini-pro",
            "confidence": 0.0
        }

def get_groq_response(question: str) -> Dict[str, Any]:
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
    except (ValueError, AttributeError) as e:
        logger.error(f"Groq client error: {e}")
        return {
            "answer": f"Groq client error: {str(e)}",
            "model": "mixtral-8x7b-32768",
            "confidence": 0.0
        }
    except Exception as e:
        logger.error(f"Unexpected Groq error: {e}")
        return {
            "answer": "Service temporarily unavailable",
            "model": "mixtral-8x7b-32768",
            "confidence": 0.0
        }

def fusion_ai_response(question: str) -> Dict[str, Any]:
    """Get fusion response from both models"""
    try:
        # Get responses from both models
        responses = []
        if gemini_client:
            responses.append(get_gemini_response(question))
        if groq_client:
            responses.append(get_groq_response(question))
        
        if not responses:
            raise ValueError("No AI models available")
        
        # Filter out error responses
        valid_responses = [r for r in responses if r.get("confidence", 0) > 0]
        
        if not valid_responses:
            # Return best error response if all failed
            return max(responses, key=lambda x: x.get("confidence", 0))
        
        # Simple fusion strategy: use highest confidence
        best_response = max(valid_responses, key=lambda x: x["confidence"])
        
        return {
            "answer": best_response["answer"],
            "model": f"fusion-ai ({best_response['model']})",
            "confidence": best_response["confidence"],
            "all_responses": valid_responses
        }
        
    except Exception as e:
        logger.error(f"Fusion AI error: {e}")
        return {
            "answer": "Fusion AI service temporarily unavailable",
            "model": "fusion-ai",
            "confidence": 0.0
        }

@app.post("/query", response_model=Answer)
async def query(q: Query):
    """Main query endpoint with AI model selection"""
    try:
        # Validate input
        q.validate_question()
        
        if q.model_preference == "gemini" and gemini_client:
            result = get_gemini_response(q.question)
        elif q.model_preference == "groq" and groq_client:
            result = get_groq_response(q.question)
        elif q.use_fusion:
            result = fusion_ai_response(q.question)
        else:
            # Default fallback
            if gemini_client:
                result = get_gemini_response(q.question)
            elif groq_client:
                result = get_groq_response(q.question)
            else:
                raise HTTPException(status_code=503, detail="No AI models available")
        
        # Implement basic RAG sources from medical knowledge
        sources = [
            {"title": "Clinical Knowledge Base", "url": "", "excerpt": "Medical knowledge repository"},
            {"title": "Medical Literature", "url": "", "excerpt": "Evidence-based medical information"},
            {"title": f"AI Model: {result['model']}", "url": "", "excerpt": "AI-generated clinical response"}
        ]
        
        return Answer(
            answer=result["answer"],
            sources=sources,
            model_used=result["model"],
            confidence_score=result["confidence"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health():
    """Legacy health check endpoint"""
    from src.api.health_checks import health_detailed_endpoint
    
    health_data = await health_detailed_endpoint()
    
    # Convert to legacy format for backward compatibility
    legacy_response = {
        "status": "ok" if health_data.get("status") == "healthy" else "error",
        "models": {},
        "fusion_ai_enabled": False
    }
    
    # Extract AI service status
    if "ai_services" in health_data.get("checks", {}):
        ai_services = health_data["checks"]["ai_services"]
        for service_name, service_data in ai_services.items():
            if isinstance(service_data, dict):
                status = service_data.get("status", "unknown")
                # Preserve 'not_configured' from detailed checks; map other non-healthy states to 'error'
                if status == "healthy":
                    legacy_response["models"][service_name] = "healthy"
                elif status == "not_configured":
                    legacy_response["models"][service_name] = "not_configured"
                else:
                    legacy_response["models"][service_name] = "error"
        
        # Check if fusion is enabled (both services healthy)
        gemini_healthy = legacy_response["models"].get("gemini") == "healthy"
        groq_healthy = legacy_response["models"].get("groq") == "healthy"
        legacy_response["fusion_ai_enabled"] = gemini_healthy and groq_healthy
    
    return legacy_response

@app.get("/healthz")
async def healthz():
    """Kubernetes liveness probe - fast health check"""
    from src.api.health_checks import healthz_endpoint, get_health_status_code
    
    health_data = await healthz_endpoint()
    status_code = get_health_status_code(health_data)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=health_data)
    
    return health_data

@app.get("/readyz") 
async def readyz():
    """Kubernetes readiness probe - comprehensive readiness check"""
    from src.api.health_checks import readyz_endpoint, get_health_status_code
    
    readiness_data = await readyz_endpoint()
    status_code = get_health_status_code(readiness_data)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=readiness_data)
    
    return readiness_data

@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check for monitoring and debugging"""
    from src.api.health_checks import health_detailed_endpoint
    
    return await health_detailed_endpoint()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HealthAI RAG - Medical AI Assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }