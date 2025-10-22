from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class FusionStrategy(str, Enum):
    """Available fusion strategies for combining AI models"""
    WEIGHTED_AVERAGE = "weighted_average"
    MAJORITY_VOTE = "majority_vote"
    BEST_CONFIDENCE = "best_confidence"


class ModelResponseModel(BaseModel):
    """Response from an individual AI model"""
    content: str = Field(..., description="The generated content from the model")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the response")
    model_name: str = Field(..., description="Name of the AI model that generated this response")
    processing_time: float = Field(..., ge=0.0, description="Time taken to generate response in seconds")
    token_count: Optional[int] = Field(None, description="Number of tokens in the response")


class FusionChatRequest(BaseModel):
    """Request for fusion AI chat"""
    message: str = Field(..., min_length=1, description="User's message/question")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    use_rag: bool = Field(True, description="Whether to use RAG for context")
    fusion_strategy: Optional[FusionStrategy] = Field(None, description="Override default fusion strategy")
    context: Optional[str] = Field(None, description="Additional context for the AI models")
    
    # Fusion-specific parameters
    require_consensus: bool = Field(False, description="Require agreement between models")
    min_confidence: float = Field(0.3, ge=0.0, le=1.0, description="Minimum confidence threshold")
    max_retries: Optional[int] = Field(None, ge=0, le=5, description="Maximum retry attempts")


class FusionProcessingDetails(BaseModel):
    """Detailed information about the fusion process"""
    total_models: int = Field(..., description="Number of models used in fusion")
    strategy_used: str = Field(..., description="Fusion strategy applied")
    response_lengths: List[int] = Field(..., description="Length of each model response")
    confidences: List[float] = Field(..., description="Confidence scores from each model")
    processing_times: List[float] = Field(..., description="Processing time for each model")
    weights_applied: Optional[List[float]] = Field(None, description="Weights used in weighted average")
    selected_model: Optional[str] = Field(None, description="Model selected for final response")
    voting_winner: Optional[str] = Field(None, description="Winner in majority voting")
    confidence_scores: Optional[Dict[str, float]] = Field(None, description="Confidence by model name")
    fallback: Optional[bool] = Field(None, description="Whether fallback mode was used")


class FusionChatResponse(BaseModel):
    """Enhanced response from fusion AI system"""
    response: str = Field(..., description="Final fused response")
    conversation_id: str = Field(..., description="Conversation identifier")
    
    # Fusion-specific fields
    fusion_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence of fused response")
    fusion_strategy: str = Field(..., description="Strategy used for fusion")
    model_responses: List[ModelResponseModel] = Field(..., description="Individual model responses")
    processing_details: FusionProcessingDetails = Field(..., description="Detailed fusion processing info")
    
    # RAG fields
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="RAG sources used")
    
    # Metadata
    total_processing_time: float = Field(..., ge=0.0, description="Total time for fusion process")
    models_used: List[str] = Field(..., description="List of AI models used")
    consensus_achieved: bool = Field(..., description="Whether models achieved consensus")


class FusionHealthStatus(BaseModel):
    """Health status of the fusion AI system"""
    fusion_enabled: bool = Field(..., description="Whether fusion AI is enabled")
    models_available: Dict[str, Dict[str, Any]] = Field(..., description="Status of each AI model")
    fusion_strategy: str = Field(..., description="Current fusion strategy")
    weights: Dict[str, float] = Field(..., description="Current model weights")
    last_health_check: Optional[str] = Field(None, description="Timestamp of last health check")


class FusionMetrics(BaseModel):
    """Performance metrics for fusion AI system"""
    total_requests: int = Field(0, description="Total fusion requests processed")
    successful_fusions: int = Field(0, description="Successful fusion operations")
    fallback_count: int = Field(0, description="Times fallback was used")
    average_confidence: float = Field(0.0, description="Average confidence score")
    average_processing_time: float = Field(0.0, description="Average processing time")
    model_usage_stats: Dict[str, int] = Field(default_factory=dict, description="Usage count per model")
    strategy_usage_stats: Dict[str, int] = Field(default_factory=dict, description="Usage count per strategy")


class FusionConfigUpdate(BaseModel):
    """Update fusion AI configuration"""
    fusion_enabled: Optional[bool] = Field(None, description="Enable/disable fusion AI")
    fusion_strategy: Optional[FusionStrategy] = Field(None, description="Change fusion strategy")
    gemini_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Update Gemini weight")
    groq_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Update Groq weight")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Update confidence threshold")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="Update max retries")


# Legacy models for backward compatibility
class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Basic chat request (legacy)"""
    message: str = Field(..., min_length=1, description="User's message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    use_rag: bool = Field(True, description="Use RAG enhancement")


class ChatResponse(BaseModel):
    """Basic chat response (legacy)"""
    response: str = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="RAG sources")