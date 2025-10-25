"""
HIPAA-Compliant User Analytics System
Privacy-first analytics for healthcare GenAI application
"""
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import boto3
from decimal import Decimal

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Healthcare-specific analytics event types"""
    USER_SESSION_START = "user_session_start"
    USER_SESSION_END = "user_session_end"
    MEDICAL_QUERY_SUBMITTED = "medical_query_submitted"
    MEDICAL_RESPONSE_RECEIVED = "medical_response_received"
    QUERY_RATED = "query_rated"
    ERROR_ENCOUNTERED = "error_encountered"
    PII_VIOLATION_BLOCKED = "pii_violation_blocked"
    PROMPT_INJECTION_BLOCKED = "prompt_injection_blocked"
    COST_LIMIT_REACHED = "cost_limit_reached"
    USER_FEEDBACK_SUBMITTED = "user_feedback_submitted"

@dataclass
class AnalyticsEvent:
    """HIPAA-compliant analytics event structure"""
    event_id: str
    event_type: EventType
    timestamp: str
    user_hash: str  # SHA256 anonymized user identifier
    session_id: str
    metadata: Dict[str, Any]
    duration_ms: Optional[int] = None
    success: bool = True
    error_code: Optional[str] = None

class UserAnalytics:
    """Privacy-first user analytics for healthcare applications"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.dynamodb = boto3.resource('dynamodb')
        
        # Initialize analytics tables
        self.events_table = 'healthai-analytics-events'
        self.sessions_table = 'healthai-user-sessions'
        self.metrics_table = 'healthai-aggregated-metrics'
        
        # Privacy settings
        self.data_retention_days = 90  # HIPAA compliance
        self.anonymization_salt = "healthai-2024-salt"  # Should be from secrets
        
        # Initialize session tracking
        self.active_sessions = {}
        
    def anonymize_user_id(self, user_id: str) -> str:
        """Create anonymized but consistent user identifier"""
        combined = f"{user_id}:{self.anonymization_salt}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def track_event(self, 
                   event_type: EventType,
                   user_id: str,
                   session_id: str,
                   metadata: Optional[Dict[str, Any]] = None,
                   duration_ms: Optional[int] = None,
                   success: bool = True,
                   error_code: Optional[str] = None) -> str:
        """Track analytics event with privacy protection"""
        
        try:
            # Create anonymized event
            event_id = f"evt_{int(time.time() * 1000)}_{hashlib.md5(user_id.encode()).hexdigest()[:8]}"
            user_hash = self.anonymize_user_id(user_id)
            
            # Sanitize metadata (remove PII)
            clean_metadata = self._sanitize_metadata(metadata or {})
            
            event = AnalyticsEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.utcnow().isoformat() + "Z",
                user_hash=user_hash,
                session_id=session_id,
                metadata=clean_metadata,
                duration_ms=duration_ms,
                success=success,
                error_code=error_code
            )
            
            # Store event in DynamoDB
            self._store_event(event)
            
            # Send real-time metrics to CloudWatch
            self._send_cloudwatch_metrics(event)
            
            # Log for audit trail
            logger.info(f"Analytics event: {event.event_type.value}", extra={
                "event_id": event_id,
                "user_hash": user_hash[:8],  # Partial hash for logs
                "success": success
            })
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to track analytics event: {e}")
            return ""
    
    def start_session(self, user_id: str, user_agent: Optional[str] = None) -> str:
        """Start user session tracking"""
        session_id = f"sess_{int(time.time())}_{hashlib.md5(user_id.encode()).hexdigest()[:8]}"
        
        # Track session start event
        metadata = {}
        if user_agent:
            # Extract safe device info (no PII)
            metadata['device_type'] = self._extract_device_type(user_agent)
            metadata['browser_family'] = self._extract_browser_family(user_agent)
        
        self.track_event(
            event_type=EventType.USER_SESSION_START,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata
        )
        
        # Store session info
        self.active_sessions[session_id] = {
            'start_time': time.time(),
            'user_hash': self.anonymize_user_id(user_id),
            'events_count': 1
        }
        
        return session_id
    
    def end_session(self, user_id: str, session_id: str):
        """End user session and calculate metrics"""
        if session_id in self.active_sessions:
            session_info = self.active_sessions[session_id]
            duration_ms = int((time.time() - session_info['start_time']) * 1000)
            
            self.track_event(
                event_type=EventType.USER_SESSION_END,
                user_id=user_id,
                session_id=session_id,
                duration_ms=duration_ms,
                metadata={'events_count': session_info['events_count']}
            )
            
            del self.active_sessions[session_id]
    
    def track_medical_query(self, 
                          user_id: str, 
                          session_id: str, 
                          query_length: int,
                          query_type: str = "general",
                          response_time_ms: Optional[int] = None,
                          success: bool = True) -> str:
        """Track medical query with healthcare-specific metrics"""
        
        metadata = {
            'query_length': query_length,
            'query_type': query_type,
            'medical_domain': True
        }
        
        if response_time_ms:
            metadata['response_time_ms'] = response_time_ms
        
        return self.track_event(
            event_type=EventType.MEDICAL_QUERY_SUBMITTED,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            duration_ms=response_time_ms,
            success=success
        )
    
    def track_security_event(self,
                           user_id: str,
                           session_id: str,
                           event_type: EventType,
                           violation_type: str,
                           risk_level: str):
        """Track security violations for analysis"""
        
        metadata = {
            'violation_type': violation_type,
            'risk_level': risk_level,
            'security_event': True
        }
        
        self.track_event(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
            success=False  # Security violations are failures
        )
    
    def get_user_analytics(self, 
                          start_date: datetime, 
                          end_date: datetime,
                          aggregation: str = "daily") -> Dict[str, Any]:
        """Get aggregated user analytics (anonymized)"""
        
        try:
            # Query DynamoDB for analytics in date range
            # This would be implemented based on your DynamoDB schema
            
            analytics = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'aggregation': aggregation
                },
                'metrics': {
                    'total_sessions': 0,
                    'total_queries': 0,
                    'avg_session_duration_ms': 0,
                    'avg_response_time_ms': 0,
                    'success_rate': 0.0,
                    'security_incidents': 0
                },
                'trends': {
                    'daily_active_users': [],
                    'query_volume_trend': [],
                    'error_rate_trend': []
                }
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            return {}
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Remove PII from metadata"""
        pii_keys = ['name', 'email', 'phone', 'address', 'ssn', 'dob', 'patient_id']
        
        sanitized = {}
        for key, value in metadata.items():
            if key.lower() not in pii_keys:
                # Also check for PII in string values
                if isinstance(value, str) and not self._contains_pii(value):
                    sanitized[key] = value
                elif not isinstance(value, str):
                    sanitized[key] = value
        
        return sanitized
    
    def _contains_pii(self, text: str) -> bool:
        """Basic PII detection in text"""
        import re
        
        # SSN pattern
        if re.search(r'\d{3}-?\d{2}-?\d{4}', text):
            return True
        
        # Phone pattern
        if re.search(r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text):
            return True
            
        # Email pattern
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            return True
        
        return False
    
    def _extract_device_type(self, user_agent: str) -> str:
        """Extract device type from user agent"""
        ua_lower = user_agent.lower()
        if 'mobile' in ua_lower or 'android' in ua_lower:
            return 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            return 'tablet'
        else:
            return 'desktop'
    
    def _extract_browser_family(self, user_agent: str) -> str:
        """Extract browser family from user agent"""
        ua_lower = user_agent.lower()
        if 'chrome' in ua_lower:
            return 'chrome'
        elif 'firefox' in ua_lower:
            return 'firefox'
        elif 'safari' in ua_lower:
            return 'safari'
        elif 'edge' in ua_lower:
            return 'edge'
        else:
            return 'other'
    
    def _store_event(self, event: AnalyticsEvent):
        """Store event in DynamoDB"""
        try:
            table = self.dynamodb.Table(self.events_table)
            
            # Convert event to DynamoDB format
            item = {
                'event_id': event.event_id,
                'timestamp': event.timestamp,
                'event_type': event.event_type.value,
                'user_hash': event.user_hash,
                'session_id': event.session_id,
                'metadata': json.dumps(event.metadata),
                'duration_ms': event.duration_ms,
                'success': event.success,
                'error_code': event.error_code,
                'ttl': int(time.time()) + (self.data_retention_days * 24 * 60 * 60)
            }
            
            # Remove None values
            item = {k: v for k, v in item.items() if v is not None}
            
            table.put_item(Item=item)
            
        except Exception as e:
            logger.error(f"Failed to store analytics event: {e}")
    
    def _send_cloudwatch_metrics(self, event: AnalyticsEvent):
        """Send real-time metrics to CloudWatch"""
        try:
            namespace = 'HealthAI/Analytics'
            
            # Base metrics
            metrics = [
                {
                    'MetricName': 'EventCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'EventType', 'Value': event.event_type.value}
                    ]
                }
            ]
            
            # Add duration metric if available
            if event.duration_ms is not None:
                metrics.append({
                    'MetricName': 'EventDuration',
                    'Value': event.duration_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'EventType', 'Value': event.event_type.value}
                    ]
                })
            
            # Add success/failure metrics
            metrics.append({
                'MetricName': 'SuccessRate',
                'Value': 1 if event.success else 0,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'EventType', 'Value': event.event_type.value}
                ]
            })
            
            self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to send CloudWatch metrics: {e}")

# Usage example for integration
class HealthAIAnalyticsMiddleware:
    """FastAPI middleware for automatic analytics tracking"""
    
    def __init__(self, analytics: UserAnalytics):
        self.analytics = analytics
    
    async def __call__(self, request, call_next):
        # Start timing
        start_time = time.time()
        
        # Extract user info
        user_id = request.headers.get('X-User-ID', 'anonymous')
        session_id = request.headers.get('X-Session-ID')
        
        if not session_id:
            session_id = self.analytics.start_session(
                user_id=user_id,
                user_agent=request.headers.get('User-Agent')
            )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Track API call
        if request.url.path.startswith('/chat'):
            self.analytics.track_event(
                event_type=EventType.MEDICAL_QUERY_SUBMITTED,
                user_id=user_id,
                session_id=session_id,
                duration_ms=duration_ms,
                success=200 <= response.status_code < 400,
                metadata={'endpoint': request.url.path}
            )
        
        # Add session ID to response headers
        response.headers['X-Session-ID'] = session_id
        
        return response