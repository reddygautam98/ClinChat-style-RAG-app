"""
Configuration for rate limiting integration with FastAPI app
"""
import redis
import os
from src.middleware.rate_limiter import HealthcareRateLimiter

def setup_rate_limiting(app):
    """Configure rate limiting middleware for healthcare API"""
    
    # Redis configuration for rate limiting
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    try:
        # Initialize Redis client
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test Redis connection
        redis_client.ping()
        
        # Add rate limiting middleware
        app.add_middleware(
            HealthcareRateLimiter,
            redis_client=redis_client,
            default_limit=100,          # 100 requests per hour
            medical_query_limit=50,     # 50 medical queries per hour
            burst_limit=10,             # 10 requests per minute burst
            window_seconds=3600         # 1 hour window
        )
        
        print("✅ Rate limiting enabled with Redis backend")
        
    except redis.RedisError as e:
        print(f"⚠️  Redis unavailable, using in-memory rate limiting: {e}")
        
        # Fallback to in-memory rate limiting
        from src.middleware.memory_rate_limiter import MemoryRateLimiter
        app.add_middleware(
            MemoryRateLimiter,
            default_limit=50,           # Lower limits for in-memory
            medical_query_limit=25,
            burst_limit=5
        )

def get_rate_limit_config():
    """Get rate limiting configuration for monitoring"""
    return {
        "healthcare_limits": {
            "medical_queries_per_hour": 50,
            "document_uploads_per_hour": 20,
            "admin_operations_per_hour": 100,
            "health_checks_per_hour": 1000,
            "burst_limit_per_minute": 10
        },
        "compliance_features": {
            "audit_logging": True,
            "client_anonymization": True,
            "security_headers": True,
            "violation_alerting": True
        }
    }