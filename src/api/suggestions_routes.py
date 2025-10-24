"""
API Routes for Query Auto-Suggestions
Provides REST endpoints for intelligent medical query suggestions
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Query as QueryParam, Depends
from pydantic import BaseModel, Field
import asyncio

from src.services.query_suggestions import AsyncQuerySuggestionEngine

# Configure logging
logger = logging.getLogger(__name__)

# Router for suggestions endpoints
suggestions_router = APIRouter(prefix="/api/v1/suggestions", tags=["Query Suggestions"])

# Global suggestion engine instance
suggestion_engine = AsyncQuerySuggestionEngine()

# Request/Response models
class SuggestionRequest(BaseModel):
    """Request model for getting suggestions"""
    query: str = Field(..., min_length=1, max_length=500, description="Partial query text")
    max_suggestions: Optional[int] = Field(8, ge=1, le=15, description="Maximum suggestions to return")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context for personalization")

class SuggestionItem(BaseModel):
    """Individual suggestion item"""
    text: str = Field(..., description="Suggested query text")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    category: str = Field(..., description="Suggestion category")
    type: str = Field(..., description="Completion type")
    domain: Optional[str] = Field(None, description="Medical domain")
    popularity: float = Field(..., ge=0, le=1, description="Popularity score")

class SuggestionsResponse(BaseModel):
    """Response model for suggestions"""
    status: str = Field(..., description="Response status")
    suggestions: List[SuggestionItem] = Field(..., description="List of suggestions")
    count: int = Field(..., description="Number of suggestions returned")
    query_info: Dict[str, Any] = Field(..., description="Query analysis information")

class LearnRequest(BaseModel):
    """Request model for learning from user interactions"""
    query: str = Field(..., min_length=1, max_length=2000, description="User query")
    user_clicked: bool = Field(False, description="Whether user clicked on a suggestion")

@suggestions_router.get("/", response_model=SuggestionsResponse)
async def get_suggestions(
    q: str = QueryParam(..., min_length=1, max_length=500, description="Partial query"),
    max_suggestions: int = QueryParam(8, ge=1, le=15, description="Max suggestions"),
    user_age_group: Optional[str] = QueryParam(None, description="User age group"),
    request: Request = None
) -> SuggestionsResponse:
    """
    Get intelligent query suggestions for partial medical query
    
    Args:
        q: Partial query text (minimum 1 character)
        max_suggestions: Maximum number of suggestions to return (1-15)
        user_age_group: Optional user age group for contextual suggestions
        request: FastAPI request object for context
        
    Returns:
        List of ranked suggestions with metadata
        
    Example:
        GET /api/v1/suggestions/?q=what%20are%20symptoms&max_suggestions=5
    """
    try:
        # Build user context
        user_context = {}
        if user_age_group:
            user_context["age_group"] = user_age_group
        
        # Add request context if available
        if request:
            user_context.update({
                "ip_address": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")[:100],
                "timestamp": asyncio.get_event_loop().time()
            })
        
        # Get suggestions
        suggestions_data = await suggestion_engine.get_suggestions_async(
            partial_query=q,
            max_suggestions=max_suggestions,
            user_context=user_context if user_context else None
        )
        
        # Convert to response format
        suggestions = [SuggestionItem(**item) for item in suggestions_data]
        
        # Query analysis info
        query_info = {
            "length": len(q),
            "word_count": len(q.split()),
            "has_medical_keywords": any(
                keyword in q.lower() 
                for keyword in ["symptoms", "treatment", "causes", "pain", "doctor", "medicine"]
            ),
            "complexity": "simple" if len(q) < 20 else ("medium" if len(q) < 100 else "complex")
        }
        
        logger.info(f"Generated {len(suggestions)} suggestions for query: '{q[:50]}...'")
        
        return SuggestionsResponse(
            status="success",
            suggestions=suggestions,
            count=len(suggestions),
            query_info=query_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get suggestions for '{q}': {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Failed to generate suggestions",
                "message": str(e),
                "suggestions": [],
                "count": 0
            }
        )

@suggestions_router.post("/", response_model=SuggestionsResponse)
async def get_suggestions_post(request_data: SuggestionRequest) -> SuggestionsResponse:
    """
    Get suggestions via POST request (supports richer context)
    
    Args:
        request_data: Suggestion request with query and context
        
    Returns:
        List of ranked suggestions with metadata
        
    Example:
        POST /api/v1/suggestions/
        {
            "query": "what are symptoms",
            "max_suggestions": 5,
            "user_context": {
                "age_group": "adult",
                "recent_queries": ["diabetes", "blood pressure"]
            }
        }
    """
    try:
        # Get suggestions using the suggestion engine
        suggestions_data = await suggestion_engine.get_suggestions_async(
            partial_query=request_data.query,
            max_suggestions=request_data.max_suggestions,
            user_context=request_data.user_context
        )
        
        # Convert to response format
        suggestions = [SuggestionItem(**item) for item in suggestions_data]
        
        # Enhanced query analysis for POST requests
        query_info = {
            "length": len(request_data.query),
            "word_count": len(request_data.query.split()),
            "has_medical_keywords": any(
                keyword in request_data.query.lower() 
                for keyword in ["symptoms", "treatment", "causes", "diagnosis", "prevention"]
            ),
            "complexity": "simple" if len(request_data.query) < 20 else ("medium" if len(request_data.query) < 100 else "complex"),
            "context_provided": request_data.user_context is not None,
            "context_keys": list(request_data.user_context.keys()) if request_data.user_context else []
        }
        
        logger.info(f"Generated {len(suggestions)} suggestions (POST) for: '{request_data.query[:50]}...'")
        
        return SuggestionsResponse(
            status="success",
            suggestions=suggestions,
            count=len(suggestions),
            query_info=query_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get suggestions (POST) for '{request_data.query}': {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to generate suggestions", 
                "message": str(e),
                "suggestions": [],
                "count": 0
            }
        )

@suggestions_router.post("/learn")
async def learn_from_query(request_data: LearnRequest) -> Dict[str, Any]:
    """
    Learn from user query interactions to improve suggestions
    
    Args:
        request_data: Learning request with query and interaction data
        
    Returns:
        Success confirmation
        
    Example:
        POST /api/v1/suggestions/learn
        {
            "query": "What are the symptoms of diabetes?",
            "user_clicked": true
        }
    """
    try:
        # Learn from the query
        await suggestion_engine.learn_from_query_async(
            query=request_data.query,
            user_clicked=request_data.user_clicked
        )
        
        logger.info(f"Learned from query: '{request_data.query[:50]}...' (clicked: {request_data.user_clicked})")
        
        return {
            "status": "success",
            "message": "Successfully learned from user interaction",
            "query_length": len(request_data.query),
            "user_clicked": request_data.user_clicked
        }
        
    except Exception as e:
        logger.error(f"Failed to learn from query '{request_data.query}': {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to learn from query",
                "message": str(e)
            }
        )

@suggestions_router.get("/popular")
async def get_popular_queries(
    limit: int = QueryParam(10, ge=1, le=50, description="Number of popular queries to return"),
    category: Optional[str] = QueryParam(None, description="Filter by medical category")
) -> Dict[str, Any]:
    """
    Get most popular medical queries
    
    Args:
        limit: Maximum number of queries to return
        category: Optional category filter (symptoms, treatment, etc.)
        
    Returns:
        List of popular queries with usage statistics
    """
    try:
        # This is a simplified version - in production, you'd query Redis/database
        popular_queries = [
            {"query": "What is diabetes?", "count": 1250, "category": "condition"},
            {"query": "How to lower blood pressure?", "count": 980, "category": "treatment"},
            {"query": "Signs of heart attack?", "count": 875, "category": "emergency"},
            {"query": "What causes anxiety?", "count": 750, "category": "mental_health"},
            {"query": "How to prevent stroke?", "count": 620, "category": "prevention"},
            {"query": "Symptoms of depression?", "count": 580, "category": "mental_health"},
            {"query": "What is high cholesterol?", "count": 520, "category": "condition"},
            {"query": "How to manage pain?", "count": 480, "category": "treatment"},
            {"query": "When to see a doctor?", "count": 420, "category": "general"},
            {"query": "What causes headaches?", "count": 380, "category": "symptoms"}
        ]
        
        # Filter by category if specified
        if category:
            popular_queries = [q for q in popular_queries if q["category"] == category]
        
        # Apply limit
        popular_queries = popular_queries[:limit]
        
        return {
            "status": "success",
            "popular_queries": popular_queries,
            "count": len(popular_queries),
            "total_available": 10,  # In production, get from database
            "filter": {"category": category} if category else {}
        }
        
    except Exception as e:
        logger.error(f"Failed to get popular queries: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve popular queries",
                "message": str(e)
            }
        )

@suggestions_router.get("/categories")
async def get_suggestion_categories() -> Dict[str, Any]:
    """
    Get available suggestion categories and medical domains
    
    Returns:
        List of categories with descriptions
    """
    try:
        categories = {
            "symptoms": {
                "description": "Symptom-related queries",
                "examples": ["What causes chest pain?", "Signs of fever?"]
            },
            "treatment": {
                "description": "Treatment and medication queries", 
                "examples": ["How to treat diabetes?", "Best medicines for anxiety?"]
            },
            "diagnosis": {
                "description": "Diagnostic process queries",
                "examples": ["How is cancer diagnosed?", "What tests for heart disease?"]
            },
            "prevention": {
                "description": "Prevention and lifestyle queries",
                "examples": ["How to prevent stroke?", "Diet for heart health?"]
            },
            "emergency": {
                "description": "Emergency and urgent care queries",
                "examples": ["Signs of heart attack?", "When to call 911?"]
            },
            "mental_health": {
                "description": "Mental health and psychological queries",
                "examples": ["What is depression?", "How to manage anxiety?"]
            },
            "general": {
                "description": "General health information queries",
                "examples": ["When to see a doctor?", "What is normal blood pressure?"]
            }
        }
        
        return {
            "status": "success",
            "categories": categories,
            "count": len(categories),
            "medical_domains": [
                "symptoms", "diagnosis", "treatment", "medication", 
                "prevention", "lifestyle", "emergency", "mental_health",
                "pediatrics", "geriatrics", "women_health", "men_health"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve categories",
                "message": str(e)
            }
        )

@suggestions_router.get("/health")
async def suggestions_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for suggestions service
    
    Returns:
        Service health status and configuration
    """
    try:
        # Test the suggestion engine
        test_suggestions = await suggestion_engine.get_suggestions_async(
            partial_query="test",
            max_suggestions=3
        )
        
        return {
            "status": "healthy",
            "service": "query-suggestions",
            "version": "1.0.0",
            "features": {
                "auto_completion": True,
                "medical_entities": True,
                "pattern_learning": True,
                "popularity_ranking": True,
                "contextual_suggestions": True
            },
            "test_result": {
                "suggestions_generated": len(test_suggestions),
                "engine_responsive": True
            },
            "dependencies": {
                "redis": suggestion_engine.engine.redis_client is not None,
                "medical_analyzer": True
            }
        }
        
    except Exception as e:
        logger.error(f"Suggestions health check failed: {e}")
        return {
            "status": "unhealthy", 
            "service": "query-suggestions",
            "error": str(e),
            "dependencies": {
                "redis": False,
                "medical_analyzer": False
            }
        }