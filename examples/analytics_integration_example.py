"""
Analytics Integration Example for HealthAI
Shows how to integrate user analytics into the FastAPI application
"""
from fastapi import FastAPI, Request, Response
from src.analytics.user_analytics import UserAnalytics, EventType
import time
import hashlib

# Initialize analytics
analytics = UserAnalytics()

@app.middleware("http")
async def analytics_middleware(request: Request, call_next):
    """Middleware to automatically track user analytics"""
    start_time = time.time()
    
    # Extract user info
    user_id = request.headers.get('X-User-ID', 'anonymous')
    session_id = request.headers.get('X-Session-ID')
    
    # Generate session if needed
    if not session_id:
        session_id = analytics.start_session(
            user_id=user_id,
            user_agent=request.headers.get('User-Agent')
        )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Track analytics based on endpoint
    if request.url.path == "/chat" and request.method == "POST":
        # Track medical query
        success = 200 <= response.status_code < 400
        
        analytics.track_medical_query(
            user_id=user_id,
            session_id=session_id,
            query_length=len(await request.body()),
            query_type="medical",
            response_time_ms=duration_ms,
            success=success
        )
        
        if not success:
            # Track error event
            analytics.track_event(
                event_type=EventType.ERROR_ENCOUNTERED,
                user_id=user_id,
                session_id=session_id,
                metadata={'status_code': response.status_code, 'endpoint': '/chat'}
            )
    
    # Add session ID to response
    response.headers['X-Session-ID'] = session_id
    
    return response

# Example enhanced chat endpoint with analytics
@app.post("/chat")
async def enhanced_chat_with_analytics(
    request: ChatRequest,
    http_request: Request
):
    """Chat endpoint with integrated analytics"""
    
    user_id = http_request.headers.get('X-User-ID', 'anonymous')
    session_id = http_request.headers.get('X-Session-ID', '')
    
    try:
        # Your existing chat logic here...
        
        # Track successful query completion
        analytics.track_event(
            event_type=EventType.MEDICAL_RESPONSE_RECEIVED,
            user_id=user_id,
            session_id=session_id,
            metadata={
                'model_used': 'gemini-1.5-pro',
                'query_type': 'medical',
                'response_length': len(response_text)
            }
        )
        
        return {"response": response_text, "session_id": session_id}
        
    except Exception as e:
        # Track error
        analytics.track_event(
            event_type=EventType.ERROR_ENCOUNTERED,
            user_id=user_id,
            session_id=session_id,
            metadata={'error': str(e), 'error_type': type(e).__name__},
            success=False
        )
        raise

# Analytics endpoint for dashboard
@app.get("/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary for dashboard"""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    summary = analytics.get_user_analytics(
        start_date=start_date,
        end_date=end_date,
        aggregation="daily"
    )
    
    return summary