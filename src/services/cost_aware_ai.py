"""
Integration wrapper for AI services with cost tracking
"""
import time
import logging
from typing import Dict, Any, Optional
from src.monitoring.ai_cost_tracker import AIModelCostTracker
import uuid

logger = logging.getLogger(__name__)

class CostAwareAIService:
    """Wrapper for AI services with integrated cost tracking"""
    
    def __init__(self):
        self.cost_tracker = AIModelCostTracker()
        
    def call_gemini_with_tracking(self, 
                                 prompt: str,
                                 model: str = "1.5-pro",
                                 user_id: str = "anonymous",
                                 query_type: str = "medical") -> Dict[str, Any]:
        """Call Gemini API with cost tracking"""
        
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Import Gemini client
            import google.generativeai as genai
            
            # Configure client (API key should be from secrets manager)
            # genai.configure(api_key=get_secret("gemini-api-key"))
            
            # Create model instance
            model_instance = genai.GenerativeModel(f'gemini-{model}')
            
            # Call API
            response = model_instance.generate_content(prompt)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Estimate token usage (Gemini doesn't always provide exact counts)
            input_tokens = self._estimate_tokens(prompt)
            output_tokens = self._estimate_tokens(response.text) if response.text else 0
            
            # Track usage and cost
            self.cost_tracker.track_ai_usage(
                service="gemini",
                model=model,
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                query_type=query_type,
                user_id=user_id,
                session_id=session_id,
                response_time_ms=response_time_ms,
                success=True
            )
            
            return {
                'success': True,
                'response': response.text,
                'session_id': session_id,
                'tokens_used': input_tokens + output_tokens,
                'response_time_ms': response_time_ms,
                'model_used': f"gemini-{model}"
            }
            
        except Exception as e:
            # Track failed request
            response_time_ms = int((time.time() - start_time) * 1000)
            
            self.cost_tracker.track_ai_usage(
                service="gemini",
                model=model,
                tokens_input=self._estimate_tokens(prompt),
                tokens_output=0,
                query_type=query_type,
                user_id=user_id,
                session_id=session_id,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Gemini API call failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'response_time_ms': response_time_ms
            }
    
    def call_groq_with_tracking(self,
                               prompt: str,
                               model: str = "mixtral-8x7b-32768",
                               user_id: str = "anonymous", 
                               query_type: str = "medical") -> Dict[str, Any]:
        """Call Groq API with cost tracking"""
        
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Import Groq client
            from groq import Groq
            
            # Initialize client (API key from secrets manager)
            # client = Groq(api_key=get_secret("groq-api-key"))
            client = Groq()  # Uses GROQ_API_KEY env var
            
            # Call API
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
            )
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Get actual token usage from response
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else self._estimate_tokens(prompt)
            output_tokens = usage.completion_tokens if usage else self._estimate_tokens(response.choices[0].message.content)
            
            # Track usage and cost
            self.cost_tracker.track_ai_usage(
                service="groq",
                model=model.replace("mixtral-8x7b-32768", "mixtral-8x7b").replace("llama3-70b-8192", "llama3-70b"),
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                query_type=query_type,
                user_id=user_id,
                session_id=session_id,
                response_time_ms=response_time_ms,
                success=True
            )
            
            return {
                'success': True,
                'response': response.choices[0].message.content,
                'session_id': session_id,
                'tokens_used': input_tokens + output_tokens,
                'response_time_ms': response_time_ms,
                'model_used': model
            }
            
        except Exception as e:
            # Track failed request
            response_time_ms = int((time.time() - start_time) * 1000)
            
            self.cost_tracker.track_ai_usage(
                service="groq",
                model=model.replace("mixtral-8x7b-32768", "mixtral-8x7b").replace("llama3-70b-8192", "llama3-70b"),
                tokens_input=self._estimate_tokens(prompt),
                tokens_output=0,
                query_type=query_type,
                user_id=user_id,
                session_id=session_id,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )
            
            logger.error(f"Groq API call failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'response_time_ms': response_time_ms
            }
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)
    
    def get_cost_optimized_model(self, query_complexity: str, budget_priority: str = "balanced") -> Dict[str, str]:
        """Recommend cost-optimized model based on query complexity and budget"""
        
        recommendations = {
            "simple": {
                "cost_priority": {"service": "groq", "model": "mixtral-8x7b-32768"},
                "balanced": {"service": "gemini", "model": "1.5-flash"},
                "performance_priority": {"service": "gemini", "model": "1.5-pro"}
            },
            "medium": {
                "cost_priority": {"service": "groq", "model": "mixtral-8x7b-32768"},
                "balanced": {"service": "groq", "model": "llama3-70b-8192"},
                "performance_priority": {"service": "gemini", "model": "1.5-pro"}
            },
            "complex": {
                "cost_priority": {"service": "groq", "model": "llama3-70b-8192"},
                "balanced": {"service": "gemini", "model": "1.5-pro"},
                "performance_priority": {"service": "gemini", "model": "1.5-pro"}
            }
        }
        
        return recommendations.get(query_complexity, {}).get(budget_priority, {"service": "gemini", "model": "1.5-flash"})

# Integration with existing chat endpoint
def enhanced_chat_with_cost_tracking(query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Enhanced chat function with cost tracking and optimization"""
    
    ai_service = CostAwareAIService()
    
    # Analyze query complexity (simple implementation)
    query_complexity = "simple" if len(query) < 100 else "medium" if len(query) < 500 else "complex"
    
    # Get cost-optimized model recommendation
    model_recommendation = ai_service.get_cost_optimized_model(query_complexity, "balanced")
    
    # Call appropriate service
    if model_recommendation["service"] == "gemini":
        result = ai_service.call_gemini_with_tracking(
            prompt=query,
            model=model_recommendation["model"],
            user_id=user_id,
            query_type="medical"
        )
    else:  # groq
        result = ai_service.call_groq_with_tracking(
            prompt=query,
            model=model_recommendation["model"],
            user_id=user_id,
            query_type="medical"
        )
    
    # Add cost optimization metadata
    result['cost_optimization'] = {
        'query_complexity': query_complexity,
        'recommended_model': model_recommendation,
        'cost_tracking_enabled': True
    }
    
    return result

# Example usage in FastAPI endpoint
async def chat_endpoint_with_cost_tracking(request_data: dict, user_id: str):
    """FastAPI endpoint with integrated cost tracking"""
    
    query = request_data.get('question', '')
    
    # Enhanced chat with cost tracking
    result = enhanced_chat_with_cost_tracking(query, user_id)
    
    if result['success']:
        return {
            'answer': result['response'],
            'model_used': result['model_used'],
            'tokens_used': result['tokens_used'],
            'response_time_ms': result['response_time_ms'],
            'session_id': result['session_id'],
            'cost_optimization': result['cost_optimization']
        }
    else:
        return {
            'error': 'Failed to process query',
            'details': result.get('error', 'Unknown error'),
            'session_id': result.get('session_id', 'unknown')
        }