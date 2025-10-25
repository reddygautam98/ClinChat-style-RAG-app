"""
Rate limiting middleware for HealthAI RAG API
Implements HIPAA-compliant rate limiting with audit logging
"""
import time
import redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import json
import logging
import hashlib

logger = logging.getLogger(__name__)

class HealthcareRateLimiter(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        redis_client: redis.Redis,
        default_limit: int = 100,  # requests per window
        window_seconds: int = 3600,  # 1 hour window
        medical_query_limit: int = 50,  # Lower limit for medical queries
        burst_limit: int = 10,  # Burst limit per minute
    ):
        super().__init__(app)
        self.redis = redis_client
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.medical_query_limit = medical_query_limit
        self.burst_limit = burst_limit
        
        # Define rate limit tiers
        self.rate_limits = {
            "/health": {"limit": 1000, "window": 3600},  # Health checks
            "/chat": {"limit": medical_query_limit, "window": 3600},  # Medical queries
            "/documents": {"limit": 20, "window": 3600},  # Document upload
            "/admin": {"limit": 100, "window": 3600},  # Admin operations
        }

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP + User-Agent hash for privacy)
        client_id = self._get_client_id(request)
        endpoint = self._get_endpoint_category(request.url.path)
        
        # Check rate limits
        if not await self._check_rate_limit(client_id, endpoint, request):
            # Log security event for audit
            await self._log_rate_limit_violation(request, client_id)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": self.window_seconds,
                    "limit_type": endpoint,
                    "compliance_note": "Request blocked for system protection"
                },
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        await self._add_rate_limit_headers(response, client_id, endpoint)
        
        return response

    def _get_client_id(self, request: Request) -> str:
        """Generate privacy-compliant client identifier"""
        ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Hash for privacy compliance
        client_string = f"{ip}:{user_agent}"
        return hashlib.sha256(client_string.encode()).hexdigest()[:16]

    def _get_endpoint_category(self, path: str) -> str:
        """Categorize endpoint for appropriate rate limiting"""
        if "/health" in path:
            return "health"
        elif "/chat" in path or "/ask" in path:
            return "medical_query"
        elif "/documents" in path or "/upload" in path:
            return "documents"
        elif "/admin" in path:
            return "admin"
        else:
            return "default"

    async def _check_rate_limit(self, client_id: str, endpoint: str, request: Request) -> bool:
        """Check if request is within rate limits"""
        current_time = int(time.time())
        
        # Get rate limit config for endpoint
        config = self.rate_limits.get(endpoint, {
            "limit": self.default_limit,
            "window": self.window_seconds
        })
        
        # Check hourly limit
        hourly_key = f"rate_limit:{client_id}:{endpoint}:{current_time // config['window']}"
        hourly_count = await self._get_count(hourly_key)
        
        if hourly_count >= config["limit"]:
            return False
        
        # Check burst limit (per minute)
        minute_key = f"burst_limit:{client_id}:{current_time // 60}"
        minute_count = await self._get_count(minute_key)
        
        if minute_count >= self.burst_limit:
            return False
        
        # Increment counters
        await self._increment_counter(hourly_key, config["window"])
        await self._increment_counter(minute_key, 60)
        
        return True

    async def _get_count(self, key: str) -> int:
        """Get current count for rate limit key"""
        try:
            count = self.redis.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Redis error getting count: {e}")
            return 0

    async def _increment_counter(self, key: str, ttl: int):
        """Increment rate limit counter"""
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            pipe.execute()
        except Exception as e:
            logger.error(f"Redis error incrementing counter: {e}")

    async def _log_rate_limit_violation(self, request: Request, client_id: str):
        """Log rate limit violation for HIPAA audit trail"""
        violation_data = {
            "timestamp": time.time(),
            "client_id": client_id,  # Already hashed for privacy
            "endpoint": request.url.path,
            "method": request.method,
            "user_agent_hash": hashlib.sha256(
                request.headers.get("user-agent", "").encode()
            ).hexdigest()[:16],
            "event_type": "RATE_LIMIT_VIOLATION",
            "severity": "WARNING"
        }
        
        # Log to security audit system
        logger.warning(f"Rate limit violation: {json.dumps(violation_data)}")
        
        # Store in Redis for monitoring dashboard
        audit_key = f"audit:rate_limit:{int(time.time())}"
        try:
            self.redis.setex(audit_key, 86400 * 7, json.dumps(violation_data))  # Keep for 7 days
        except Exception as e:
            logger.error(f"Failed to store audit log: {e}")

    async def _add_rate_limit_headers(self, response, client_id: str, endpoint: str):
        """Add rate limit headers to response"""
        config = self.rate_limits.get(endpoint, {
            "limit": self.default_limit,
            "window": self.window_seconds
        })
        
        current_time = int(time.time())
        window_key = f"rate_limit:{client_id}:{endpoint}:{current_time // config['window']}"
        current_count = await self._get_count(window_key)
        
        response.headers["X-RateLimit-Limit"] = str(config["limit"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, config["limit"] - current_count))
        response.headers["X-RateLimit-Reset"] = str((current_time // config["window"] + 1) * config["window"])