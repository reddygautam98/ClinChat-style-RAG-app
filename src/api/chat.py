from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from src.models.fusion_models import (
    FusionChatRequest, 
    FusionChatResponse, 
    ChatRequest, 
    ChatResponse,
    FusionHealthStatus,
    FusionMetrics
)
from src.services.fusion_ai import fusion_ai_service
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/fusion", response_model=FusionChatResponse)
async def fusion_chat_endpoint(request: FusionChatRequest):
    """
    Advanced chat endpoint using Fusion AI technology
    Combines multiple AI models for enhanced responses
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing fusion chat request: {request.message[:50]}...")
        
        # Generate fusion response
        fusion_result = await fusion_ai_service.fusion_generate(
            prompt=request.message,
            context=request.context or ""
        )
        
        total_time = time.time() - start_time
        
        # Convert to response model
        response = FusionChatResponse(
            response=fusion_result.final_response,
            conversation_id=request.conversation_id or "default",
            fusion_confidence=fusion_result.confidence_score,
            fusion_strategy=fusion_result.fusion_strategy,
            model_responses=[
                {
                    "content": mr.content,
                    "confidence": mr.confidence,
                    "model_name": mr.model_name,
                    "processing_time": mr.processing_time,
                    "token_count": mr.token_count
                }
                for mr in fusion_result.model_responses
            ],
            processing_details=fusion_result.processing_details,
            sources=None,  # TODO: Integrate RAG sources
            total_processing_time=total_time,
            models_used=[mr.model_name for mr in fusion_result.model_responses],
            consensus_achieved=len(set(mr.content[:100] for mr in fusion_result.model_responses)) <= 2
        )
        
        logger.info(f"Fusion chat completed in {total_time:.2f}s with confidence {fusion_result.confidence_score:.2f}")
        return response
        
    except Exception as e:
        logger.error(f"Fusion chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Fusion AI error: {str(e)}")


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Basic chat endpoint (legacy support)
    Automatically uses fusion AI if enabled
    """
    try:
        # Convert to fusion request
        fusion_request = FusionChatRequest(
            message=request.message,
            conversation_id=request.conversation_id,
            use_rag=request.use_rag
        )
        
        # Use fusion AI
        fusion_response = await fusion_chat_endpoint(fusion_request)
        
        # Convert back to simple response
        return ChatResponse(
            response=fusion_response.response,
            conversation_id=fusion_response.conversation_id,
            sources=fusion_response.sources
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        # Fallback response
        return ChatResponse(
            response=f"I apologize, but I'm experiencing technical difficulties. Please try again later. (Error: {str(e)[:100]})",
            conversation_id=request.conversation_id or "default",
            sources=[]
        )


@router.get("/fusion/health")
async def get_fusion_health():
    """
    Get health status of the fusion AI system
    """
    try:
        health_status = await fusion_ai_service.get_fusion_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/fusion/models")
async def list_available_models():
    """
    List all available AI models and their status
    """
    try:
        health_status = await fusion_ai_service.get_fusion_health_status()
        return {
            "models": health_status["models_available"],
            "fusion_enabled": health_status["fusion_enabled"],
            "current_strategy": health_status["fusion_strategy"]
        }
    except Exception as e:
        logger.error(f"Models list error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Retrieve conversation history
    """
    # Placeholder implementation
    return {"conversation_id": conversation_id, "messages": []}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation
    """
    # Placeholder implementation
    return {"message": f"Conversation {conversation_id} deleted"}