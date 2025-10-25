"""
Integration of enhanced input validation with FastAPI routes
"""
from fastapi import HTTPException, Request
from src.validation.medical_input_validator import MedicalInputValidator, EnhancedMedicalQuery
import logging

logger = logging.getLogger(__name__)

class ValidationMiddleware:
    """Middleware to handle input validation for medical queries"""
    
    def __init__(self):
        self.validator = MedicalInputValidator()
    
    async def validate_medical_request(self, request: Request, query_data: dict):
        """
        Validate incoming medical request
        
        Args:
            request: FastAPI request object
            query_data: Dictionary containing query data
            
        Returns:
            Validated and sanitized query data
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            # Create enhanced query object for validation
            validated_query = EnhancedMedicalQuery(**query_data)
            
            # Additional validation for the raw question
            validation_result = self.validator.validate_medical_query(
                query_data.get('question', ''),
                user_context={
                    'ip_address': request.client.host if request.client else 'unknown',
                    'user_agent': request.headers.get('user-agent', 'unknown')
                }
            )
            
            # Block high-risk queries
            if validation_result.risk_level in ['HIGH', 'CRITICAL']:
                logger.warning(f"Blocked high-risk query: {validation_result.violations}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Query validation failed",
                        "risk_level": validation_result.risk_level,
                        "violations": validation_result.violations,
                        "compliance_note": "Request blocked for safety and compliance"
                    }
                )
            
            # Return validated data with metadata
            return {
                **validated_query.dict(),
                "validation_metadata": {
                    "medical_context_score": validation_result.medical_context_score,
                    "risk_level": validation_result.risk_level,
                    "sanitized": validation_result.sanitized_input != query_data.get('question', '')
                }
            }
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Input validation failed",
                    "message": str(e),
                    "compliance_note": "Please ensure your query does not contain sensitive information"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Validation service error",
                    "compliance_note": "Please try again or contact support"
                }
            )

# Usage in FastAPI routes
async def enhanced_chat_endpoint(request: Request, query: dict):
    """Enhanced chat endpoint with comprehensive validation"""
    
    validation_middleware = ValidationMiddleware()
    
    # Validate input
    validated_data = await validation_middleware.validate_medical_request(request, query)
    
    # Extract validated query
    sanitized_question = validated_data['question']
    validation_metadata = validated_data['validation_metadata']
    
    # Log for compliance audit
    logger.info(f"Processing validated medical query with risk level: {validation_metadata['risk_level']}")
    
    # Continue with normal processing...
    return {
        "status": "validated",
        "query": sanitized_question,
        "metadata": validation_metadata
    }