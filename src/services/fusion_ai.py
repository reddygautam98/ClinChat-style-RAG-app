from typing import Dict, List, Optional, Tuple
import asyncio
import statistics
from dataclasses import dataclass
import google.generativeai as genai
from groq import Groq
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    content: str
    confidence: float
    model_name: str
    processing_time: float
    token_count: Optional[int] = None


@dataclass
class FusionResult:
    final_response: str
    confidence_score: float
    model_responses: List[ModelResponse]
    fusion_strategy: str
    processing_details: Dict


class FusionAIService:
    """
    Advanced Fusion AI service that combines multiple AI models for enhanced responses.
    Supports various fusion strategies: weighted average, majority vote, and confidence-based selection.
    """
    
    def __init__(self):
        self.gemini_client = None
        self.groq_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI model clients"""
        try:
            if settings.GOOGLE_GEMINI_API_KEY:
                genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("Gemini client initialized successfully")
            
            if settings.GROQ_API_KEY:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info("Groq client initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing AI clients: {e}")
    
    async def get_gemini_response(self, prompt: str, context: str = "") -> ModelResponse:
        """Get response from Google Gemini"""
        import time
        start_time = time.time()
        
        try:
            full_prompt = f"{context}\n\nUser Query: {prompt}" if context else prompt
            response = self.gemini_client.generate_content(full_prompt)
            
            processing_time = time.time() - start_time
            
            # Calculate confidence based on response length and coherence (simplified)
            confidence = min(0.9, len(response.text) / 1000 + 0.3)
            
            return ModelResponse(
                content=response.text,
                confidence=confidence,
                model_name="gemini-2.5-flash",
                processing_time=processing_time,
                token_count=len(response.text.split())
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return ModelResponse(
                content=f"Gemini error: {str(e)}",
                confidence=0.0,
                model_name="gemini-2.5-flash",
                processing_time=time.time() - start_time
            )
    
    async def get_groq_response(self, prompt: str, context: str = "") -> ModelResponse:
        """Get response from Groq"""
        import time
        start_time = time.time()
        
        try:
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated to current available model
                messages=messages,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            processing_time = time.time() - start_time
            content = response.choices[0].message.content
            
            # Calculate confidence based on response quality metrics
            confidence = min(0.9, len(content) / 800 + 0.4)
            
            return ModelResponse(
                content=content,
                confidence=confidence,
                model_name="llama-3.3-70b-versatile",
                processing_time=processing_time,
                token_count=response.usage.total_tokens if response.usage else len(content.split())
            )
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return ModelResponse(
                content=f"Groq error: {str(e)}",
                confidence=0.0,
                model_name="llama-3.3-70b-versatile",
                processing_time=time.time() - start_time
            )
    
    async def fusion_generate(self, prompt: str, context: str = "") -> FusionResult:
        """
        Generate response using fusion AI technology combining multiple models
        """
        if not settings.FUSION_AI_ENABLED:
            # Fallback to single model if fusion is disabled
            response = await self.get_gemini_response(prompt, context)
            return FusionResult(
                final_response=response.content,
                confidence_score=response.confidence,
                model_responses=[response],
                fusion_strategy="single_model",
                processing_details={"fallback": True}
            )
        
        # Get responses from all available models concurrently
        tasks = []
        if self.gemini_client:
            tasks.append(self.get_gemini_response(prompt, context))
        if self.groq_client:
            tasks.append(self.get_groq_response(prompt, context))
        
        if not tasks:
            raise ValueError("No AI models available")
        
        model_responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and failed responses
        valid_responses = [
            resp for resp in model_responses 
            if isinstance(resp, ModelResponse) and resp.confidence > 0
        ]
        
        if not valid_responses:
            raise ValueError("All AI models failed to generate responses")
        
        # Apply fusion strategy
        fusion_result = self._apply_fusion_strategy(valid_responses, settings.FUSION_STRATEGY)
        
        return fusion_result
    
    def _apply_fusion_strategy(self, responses: List[ModelResponse], strategy: str) -> FusionResult:
        """Apply the specified fusion strategy to combine model responses"""
        
        processing_details = {
            "total_models": len(responses),
            "strategy_used": strategy,
            "response_lengths": [len(r.content) for r in responses],
            "confidences": [r.confidence for r in responses],
            "processing_times": [r.processing_time for r in responses]
        }
        
        if strategy == "weighted_average":
            return self._weighted_average_fusion(responses, processing_details)
        elif strategy == "majority_vote":
            return self._majority_vote_fusion(responses, processing_details)
        elif strategy == "best_confidence":
            return self._best_confidence_fusion(responses, processing_details)
        else:
            # Default to weighted average
            return self._weighted_average_fusion(responses, processing_details)
    
    def _weighted_average_fusion(self, responses: List[ModelResponse], details: Dict) -> FusionResult:
        """Combine responses using weighted averaging based on model weights"""
        
        weights = []
        contents = []
        
        for response in responses:
            if "gemini" in response.model_name.lower():
                weights.append(settings.GEMINI_WEIGHT * response.confidence)
            elif "llama" in response.model_name.lower() or "groq" in response.model_name.lower():
                weights.append(settings.GROQ_WEIGHT * response.confidence)
            else:
                weights.append(0.5 * response.confidence)  # Default weight
            
            contents.append(response.content)
        
        # Select the response with highest weighted confidence
        max_weight_idx = weights.index(max(weights))
        final_response = contents[max_weight_idx]
        
        # Calculate overall confidence
        avg_confidence = sum(weights) / len(weights)
        
        details["weights_applied"] = weights
        details["selected_model"] = responses[max_weight_idx].model_name
        
        return FusionResult(
            final_response=final_response,
            confidence_score=avg_confidence,
            model_responses=responses,
            fusion_strategy="weighted_average",
            processing_details=details
        )
    
    def _majority_vote_fusion(self, responses: List[ModelResponse], details: Dict) -> FusionResult:
        """Combine responses using majority voting (simplified implementation)"""
        
        # For text responses, we'll use the one with median length and highest confidence
        sorted_responses = sorted(responses, key=lambda x: x.confidence, reverse=True)
        final_response = sorted_responses[0].content
        
        avg_confidence = statistics.mean([r.confidence for r in responses])
        
        details["voting_winner"] = sorted_responses[0].model_name
        
        return FusionResult(
            final_response=final_response,
            confidence_score=avg_confidence,
            model_responses=responses,
            fusion_strategy="majority_vote",
            processing_details=details
        )
    
    def _best_confidence_fusion(self, responses: List[ModelResponse], details: Dict) -> FusionResult:
        """Select the response with the highest confidence score"""
        
        best_response = max(responses, key=lambda x: x.confidence)
        
        details["selected_model"] = best_response.model_name
        details["confidence_scores"] = {r.model_name: r.confidence for r in responses}
        
        return FusionResult(
            final_response=best_response.content,
            confidence_score=best_response.confidence,
            model_responses=responses,
            fusion_strategy="best_confidence",
            processing_details=details
        )
    
    async def get_fusion_health_status(self) -> Dict:
        """Check the health status of all AI models"""
        status = {
            "fusion_enabled": settings.FUSION_AI_ENABLED,
            "models_available": {},
            "fusion_strategy": settings.FUSION_STRATEGY,
            "weights": {
                "gemini": settings.GEMINI_WEIGHT,
                "groq": settings.GROQ_WEIGHT
            }
        }
        
        # Test Gemini
        if self.gemini_client:
            try:
                test_response = await self.get_gemini_response("Hello")
                status["models_available"]["gemini"] = {
                    "status": "healthy" if test_response.confidence > 0 else "error",
                    "response_time": test_response.processing_time
                }
            except Exception as e:
                status["models_available"]["gemini"] = {"status": "error", "error": str(e)}
        
        # Test Groq
        if self.groq_client:
            try:
                test_response = await self.get_groq_response("Hello")
                status["models_available"]["groq"] = {
                    "status": "healthy" if test_response.confidence > 0 else "error",
                    "response_time": test_response.processing_time
                }
            except Exception as e:
                status["models_available"]["groq"] = {"status": "error", "error": str(e)}
        
        return status


# Global fusion AI service instance
fusion_ai_service = FusionAIService()