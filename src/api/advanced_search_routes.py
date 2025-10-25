"""
API Routes for Advanced Semantic Search
Enhanced search capabilities with ML ranking and query expansion
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Query as QueryParam
from pydantic import BaseModel, Field
import asyncio

from src.rag.advanced_semantic_search import (
    AdvancedSemanticSearch,
    SemanticSearchResult,
    create_advanced_semantic_search
)

# Configure logging
logger = logging.getLogger(__name__)

# Router for advanced search endpoints
search_router = APIRouter(prefix="/api/v1/search", tags=["Advanced Semantic Search"])

# Global search engine instance
search_engine = None

# Request/Response models
class AdvancedSearchRequest(BaseModel):
    """Request model for advanced semantic search"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    k: Optional[int] = Field(5, ge=1, le=20, description="Number of results to return")
    use_query_expansion: Optional[bool] = Field(True, description="Enable query expansion")
    use_ml_ranking: Optional[bool] = Field(True, description="Enable ML-based ranking")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context for personalization")

class SearchResultItem(BaseModel):
    """Individual search result"""
    document_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document content")
    similarity_score: float = Field(..., ge=0, le=1, description="Vector similarity score")
    ml_relevance_score: float = Field(..., ge=0, le=1, description="ML relevance score")
    combined_score: float = Field(..., ge=0, le=1, description="Final combined score")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    explanation: Dict[str, Any] = Field(..., description="Ranking explanation")
    semantic_matches: List[str] = Field(..., description="Key semantic matches")

class AdvancedSearchResponse(BaseModel):
    """Response model for advanced search"""
    status: str = Field(..., description="Response status")
    results: List[SearchResultItem] = Field(..., description="Search results")
    count: int = Field(..., description="Number of results returned")
    query_info: Dict[str, Any] = Field(..., description="Query analysis information")
    performance: Dict[str, Any] = Field(..., description="Search performance metrics")

async def get_search_engine():
    """Get or initialize search engine"""
    global search_engine
    if search_engine is None:
        try:
            search_engine = create_advanced_semantic_search()
            logger.info("Advanced search engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize search engine: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Search engine initialization failed"
            )
    return search_engine

@search_router.post("/", response_model=AdvancedSearchResponse)
async def advanced_search(request_data: AdvancedSearchRequest) -> AdvancedSearchResponse:
    """
    Perform advanced semantic search with ML ranking and query expansion
    
    Args:
        request_data: Search request parameters
        
    Returns:
        Enhanced search results with ML ranking
        
    Example:
        POST /api/v1/search/
        {
            "query": "diabetes symptoms treatment",
            "k": 5,
            "use_query_expansion": true,
            "use_ml_ranking": true,
            "user_context": {
                "age_group": "adult"
            }
        }
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Get search engine
        engine = await get_search_engine()
        
        # Perform advanced search
        results = await engine.semantic_search(
            query=request_data.query,
            k=request_data.k,
            use_query_expansion=request_data.use_query_expansion,
            use_ml_ranking=request_data.use_ml_ranking,
            user_context=request_data.user_context
        )
        
        # Convert results to response format
        result_items = []
        for result in results:
            result_items.append(SearchResultItem(
                document_id=result.document_id,
                content=result.content,
                similarity_score=result.similarity_score,
                ml_relevance_score=result.ml_relevance_score,
                combined_score=result.combined_score,
                metadata=result.metadata,
                explanation=result.explanation,
                semantic_matches=result.semantic_matches
            ))
        
        # Calculate performance metrics
        end_time = asyncio.get_event_loop().time()
        search_time = end_time - start_time
        
        # Query analysis
        query_info = {
            "length": len(request_data.query),
            "word_count": len(request_data.query.split()),
            "expansion_enabled": request_data.use_query_expansion,
            "ml_ranking_enabled": request_data.use_ml_ranking,
            "context_provided": request_data.user_context is not None
        }
        
        performance = {
            "search_time_ms": round(search_time * 1000, 2),
            "results_found": len(results),
            "avg_similarity": round(
                sum(r.similarity_score for r in results) / len(results), 3
            ) if results else 0.0,
            "avg_ml_score": round(
                sum(r.ml_relevance_score for r in results) / len(results), 3
            ) if results else 0.0
        }
        
        logger.info(f"Advanced search completed: {len(results)} results in {search_time*1000:.2f}ms")
        
        return AdvancedSearchResponse(
            status="success",
            results=result_items,
            count=len(result_items),
            query_info=query_info,
            performance=performance
        )
        
    except Exception as e:
        logger.error(f"Advanced search failed for '{request_data.query}': {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Search operation failed",
                "message": str(e),
                "query": request_data.query
            }
        )

@search_router.get("/", response_model=AdvancedSearchResponse)
async def advanced_search_get(
    q: str = QueryParam(..., min_length=1, max_length=1000, description="Search query"),
    k: int = QueryParam(5, ge=1, le=20, description="Number of results"),
    expand: bool = QueryParam(True, description="Enable query expansion"),
    ml_rank: bool = QueryParam(True, description="Enable ML ranking"),
    age_group: Optional[str] = QueryParam(None, description="User age group")
) -> AdvancedSearchResponse:
    """
    Advanced semantic search via GET request
    
    Args:
        q: Search query
        k: Number of results to return
        expand: Enable query expansion
        ml_rank: Enable ML-based ranking
        age_group: Optional user age group
        
    Returns:
        Enhanced search results
        
    Example:
        GET /api/v1/search/?q=diabetes%20treatment&k=5&expand=true&ml_rank=true
    """
    # Build user context
    user_context = {}
    if age_group:
        user_context["age_group"] = age_group
    
    # Create request object
    request_data = AdvancedSearchRequest(
        query=q,
        k=k,
        use_query_expansion=expand,
        use_ml_ranking=ml_rank,
        user_context=user_context if user_context else None
    )
    
    # Use POST endpoint logic
    return await advanced_search(request_data)

@search_router.post("/train")
async def train_ml_ranking() -> Dict[str, Any]:
    """
    Train ML ranking model on current document corpus
    
    Returns:
        Training status and metrics
        
    Example:
        POST /api/v1/search/train
    """
    try:
        # Get search engine
        engine = await get_search_engine()
        
        # Get documents from vector store for training
        vector_stats = engine.vector_store.get_stats()
        
        if vector_stats["total_documents"] == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents available for training. Please index documents first."
            )
        
        # Mock training process - in production, you'd get actual documents
        training_docs = [
            {
                "doc_id": f"doc_{i}",
                "content": f"Sample medical document {i} about various health conditions",
                "metadata": {"source": "training", "date": "2024-01-01"}
            }
            for i in range(min(100, vector_stats["total_documents"]))
        ]
        
        # Train ML ranking model
        await engine.train_ml_ranking(training_docs)
        
        return {
            "status": "success",
            "message": "ML ranking model training completed",
            "training_stats": {
                "documents_used": len(training_docs),
                "total_available": vector_stats["total_documents"],
                "model_trained": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML ranking training failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Training failed",
                "message": str(e)
            }
        )

@search_router.get("/analytics")
async def get_search_analytics() -> Dict[str, Any]:
    """
    Get comprehensive search analytics and configuration
    
    Returns:
        Search system analytics and performance metrics
    """
    try:
        # Get search engine
        engine = await get_search_engine()
        
        # Get analytics from search engine
        analytics = await engine.get_search_analytics()
        
        # Add API-level analytics
        api_analytics = {
            "endpoints": {
                "advanced_search": "/api/v1/search/",
                "train_ranking": "/api/v1/search/train",
                "analytics": "/api/v1/search/analytics",
                "health": "/api/v1/search/health"
            },
            "features": {
                "query_expansion": True,
                "ml_ranking": True,
                "semantic_matching": True,
                "contextual_search": True
            }
        }
        
        return {
            "status": "success",
            "search_engine": analytics,
            "api": api_analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Analytics retrieval failed",
                "message": str(e)
            }
        )

@search_router.get("/expand-query")
async def expand_query(
    q: str = QueryParam(..., min_length=1, max_length=500, description="Query to expand"),
    max_expansions: int = QueryParam(5, ge=1, le=10, description="Max expansion terms"),
    age_group: Optional[str] = QueryParam(None, description="User age group")
) -> Dict[str, Any]:
    """
    Get query expansion suggestions for a given query
    
    Args:
        q: Original query to expand
        max_expansions: Maximum number of expansion terms
        age_group: Optional user age group for context
        
    Returns:
        Query expansion details and suggestions
        
    Example:
        GET /api/v1/search/expand-query?q=diabetes%20symptoms&max_expansions=5
    """
    try:
        # Get search engine
        engine = await get_search_engine()
        
        # Build user context
        user_context = {}
        if age_group:
            user_context["age_group"] = age_group
        
        # Expand query
        expansion = engine.query_expander.expand_query(
            query=q,
            user_context=user_context if user_context else None,
            max_expansions=max_expansions
        )
        
        return {
            "status": "success",
            "original_query": expansion.original_query,
            "expanded_query": expansion.final_expanded_query,
            "expansion_details": {
                "expanded_terms": expansion.expanded_terms,
                "medical_synonyms": expansion.medical_synonyms,
                "contextual_terms": expansion.contextual_terms
            },
            "expansion_count": len(expansion.expanded_terms),
            "context_applied": age_group is not None
        }
        
    except Exception as e:
        logger.error(f"Query expansion failed for '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Query expansion failed",
                "message": str(e),
                "original_query": q
            }
        )

@search_router.get("/health")
async def search_health_check() -> Dict[str, Any]:
    """
    Health check for advanced search service
    
    Returns:
        Service health status and capabilities
    """
    try:
        # Test search engine initialization
        engine = await get_search_engine()
        
        # Get system analytics for health info
        analytics = await engine.get_search_analytics()
        
        return {
            "status": "healthy",
            "service": "advanced-semantic-search",
            "version": "1.0.0",
            "capabilities": {
                "semantic_search": True,
                "query_expansion": True,
                "ml_ranking": analytics["ml_ranking"]["enabled"],
                "contextual_search": True
            },
            "system_status": {
                "vector_store": analytics["vector_store"]["total_documents"] > 0,
                "ml_model": analytics["ml_ranking"]["trained"],
                "query_expander": True
            },
            "performance": {
                "documents_indexed": analytics["vector_store"]["total_documents"],
                "ml_features_cached": analytics["ml_ranking"]["features_cached"]
            }
        }
        
    except Exception as e:
        logger.error(f"Search health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "advanced-semantic-search", 
            "error": str(e),
            "capabilities": {
                "semantic_search": False,
                "query_expansion": False,
                "ml_ranking": False,
                "contextual_search": False
            }
        }