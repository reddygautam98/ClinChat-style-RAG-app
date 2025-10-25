"""
HIPAA Compliance Framework for HealthAI RAG Application
Implements comprehensive HIPAA safeguards and audit controls
"""
import json
import logging
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import boto3
from enum import Enum

# Configure HIPAA-compliant logging
class HIPAALogger:
    """HIPAA-compliant logging with encryption and audit trails"""
    
    def __init__(self, encryption_key: bytes):
        self.logger = logging.getLogger("HIPAA_AUDIT")
        self.cipher_suite = Fernet(encryption_key)
        
        # Configure secure file handler
        handler = logging.FileHandler('/var/log/healthai/hipaa_audit.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

class PHIEventType(Enum):
    """Types of PHI-related events for audit logging"""
    ACCESS_GRANTED = "PHI_ACCESS_GRANTED"
    ACCESS_DENIED = "PHI_ACCESS_DENIED"
    DATA_CREATED = "PHI_DATA_CREATED"
    DATA_MODIFIED = "PHI_DATA_MODIFIED"
    DATA_VIEWED = "PHI_DATA_VIEWED"
    DATA_DELETED = "PHI_DATA_DELETED"
    EXPORT_REQUESTED = "PHI_EXPORT_REQUESTED"
    BREACH_DETECTED = "PHI_BREACH_DETECTED"
    ENCRYPTION_KEY_ROTATED = "ENCRYPTION_KEY_ROTATED"

@dataclass
class HIPAAAuditEvent:
    """HIPAA audit event structure"""
    timestamp: str
    event_type: PHIEventType
    user_id: str  # Hashed for privacy
    session_id: str
    resource_type: str
    resource_id: str  # Hashed PHI identifier
    action_performed: str
    ip_address_hash: str
    user_agent_hash: str
    success: bool
    failure_reason: Optional[str] = None
    data_classification: str = "PHI"  # PHI, PII, PUBLIC
    compliance_flags: List[str] = None

class HIPAAComplianceManager:
    """Central manager for HIPAA compliance operations"""
    
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
        self.encryption_key = self._derive_encryption_key()
        self.audit_logger = HIPAALogger(self.encryption_key)
        self.s3_client = boto3.client('s3')
        
        # HIPAA required retention periods
        self.AUDIT_RETENTION_YEARS = 6
        self.ACCESS_LOG_RETENTION_DAYS = 90
        
    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from master key using PBKDF2"""
        salt = b'healthai_hipaa_salt_2024'  # Use proper random salt in production
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return key
    
    def encrypt_phi_data(self, data: str) -> str:
        """Encrypt PHI data for storage"""
        cipher_suite = Fernet(self.encryption_key)
        encrypted_data = cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_phi_data(self, encrypted_data: str) -> str:
        """Decrypt PHI data for authorized access"""
        cipher_suite = Fernet(self.encryption_key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = cipher_suite.decrypt(encrypted_bytes)
        return decrypted_data.decode()
    
    def log_phi_access(self, event: HIPAAAuditEvent):
        """Log PHI access for HIPAA audit compliance"""
        
        # Encrypt sensitive audit data
        encrypted_event = self._encrypt_audit_event(event)
        
        # Log to local secure file
        self.audit_logger.logger.info(json.dumps(encrypted_event))
        
        # Store in S3 for long-term retention
        self._store_audit_event_s3(encrypted_event)
        
        # Send to CloudTrail for additional compliance
        self._send_to_cloudtrail(event)
    
    def _encrypt_audit_event(self, event: HIPAAAuditEvent) -> Dict:
        """Encrypt sensitive fields in audit event"""
        event_dict = asdict(event)
        
        # Fields that need encryption
        sensitive_fields = ['user_id', 'resource_id', 'ip_address_hash']
        
        for field in sensitive_fields:
            if event_dict.get(field):
                event_dict[field] = self.encrypt_phi_data(str(event_dict[field]))
        
        event_dict['encrypted'] = True
        return event_dict
    
    def _store_audit_event_s3(self, encrypted_event: Dict):
        """Store audit event in S3 with proper retention and encryption"""
        
        # Generate partition key for efficient querying
        date_partition = datetime.utcnow().strftime("%Y/%m/%d")
        hour_partition = datetime.utcnow().strftime("%H")
        
        # S3 key with proper partitioning
        s3_key = f"hipaa-audit-logs/{date_partition}/{hour_partition}/{encrypted_event.get('session_id', 'unknown')}.json"
        
        try:
            # Store with server-side encryption
            self.s3_client.put_object(
                Bucket='healthai-hipaa-audit-logs',
                Key=s3_key,
                Body=json.dumps(encrypted_event),
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId='arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012',
                Metadata={
                    'retention-class': 'hipaa-audit',
                    'compliance-level': 'phi-audit',
                    'created-date': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            # Log storage failure but don't expose sensitive data
            self.audit_logger.logger.error(f"Audit log storage failed: {type(e).__name__}")
    
    def _send_to_cloudtrail(self, event: HIPAAAuditEvent):
        """Send compliance event to AWS CloudTrail"""
        
        cloudtrail = boto3.client('cloudtrail')
        
        try:
            # Create CloudTrail event for HIPAA compliance
            cloudtrail.put_events(
                Records=[{
                    'EventTime': datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')),
                    'EventName': f'HealthAI-{event.event_type.value}',
                    'EventSource': 'healthai.hipaa.compliance',
                    'Username': hashlib.sha256(event.user_id.encode()).hexdigest()[:16],
                    'Resources': [{
                        'ResourceType': event.resource_type,
                        'ResourceName': hashlib.sha256(event.resource_id.encode()).hexdigest()[:16]
                    }],
                    'CloudTrailEvent': json.dumps({
                        'event_type': event.event_type.value,
                        'success': event.success,
                        'data_classification': event.data_classification,
                        'compliance_framework': 'HIPAA'
                    })
                }]
            )
        except Exception as e:
            self.audit_logger.logger.error(f"CloudTrail logging failed: {type(e).__name__}")
    
    def create_access_control_policy(self) -> Dict:
        """Generate HIPAA-compliant access control policy"""
        
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "HIPAAMinimumNecessary",
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::123456789012:role/HealthAI-Application-Role"},
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject"
                    ],
                    "Resource": "arn:aws:s3:::healthai-phi-data/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-server-side-encryption": "aws:kms"
                        },
                        "IpAddress": {
                            "aws:SourceIp": ["10.0.0.0/8", "172.16.0.0/12"]  # Internal IP ranges only
                        }
                    }
                },
                {
                    "Sid": "HIPAAAuditLogging",
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::123456789012:role/HealthAI-Audit-Role"},
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:log-group:/aws/healthai/hipaa-audit"
                }
            ]
        }
    
    def perform_access_control_check(self, user_id: str, resource_type: str, action: str) -> bool:
        """Perform HIPAA minimum necessary access control check"""
        
        # Hash user ID for privacy
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        
        # Define minimum necessary access rules
        access_rules = {
            "medical_query": ["read", "create"],
            "patient_data": ["read"],  # No create/update for AI system
            "audit_log": ["read"],  # Only for compliance officers
            "system_config": ["read", "update"]  # Only for admins
        }
        
        # Check if access is allowed
        allowed_actions = access_rules.get(resource_type, [])
        access_granted = action.lower() in allowed_actions
        
        # Log access attempt
        audit_event = HIPAAAuditEvent(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            event_type=PHIEventType.ACCESS_GRANTED if access_granted else PHIEventType.ACCESS_DENIED,
            user_id=user_hash,
            session_id=f"session_{datetime.utcnow().timestamp()}",
            resource_type=resource_type,
            resource_id=hashlib.sha256(f"{resource_type}_{action}".encode()).hexdigest()[:16],
            action_performed=action,
            ip_address_hash="ip_hash_placeholder",
            user_agent_hash="ua_hash_placeholder",
            success=access_granted,
            failure_reason=None if access_granted else "Minimum necessary standard not met",
            compliance_flags=["HIPAA_MINIMUM_NECESSARY"]
        )
        
        self.log_phi_access(audit_event)
        
        return access_granted
    
    def generate_breach_detection_rules(self) -> List[Dict]:
        """Generate rules for detecting potential HIPAA breaches"""
        
        return [
            {
                "rule_name": "Unusual_Access_Pattern",
                "description": "Detect unusual access patterns to PHI",
                "conditions": {
                    "access_frequency": "> 100 requests/hour",
                    "user_behavior": "deviation from baseline > 3 std dev",
                    "time_of_access": "outside business hours"
                },
                "actions": ["alert_security_team", "temporary_access_suspension"],
                "severity": "HIGH"
            },
            {
                "rule_name": "Bulk_Data_Export",
                "description": "Detect unauthorized bulk data export attempts",
                "conditions": {
                    "export_size": "> 1000 records",
                    "export_frequency": "> 5 exports/day",
                    "user_authorization": "not in export_authorized_roles"
                },
                "actions": ["block_export", "immediate_alert", "audit_investigation"],
                "severity": "CRITICAL"
            },
            {
                "rule_name": "PII_Data_Exposure",
                "description": "Detect potential PII exposure in system logs",
                "conditions": {
                    "log_content": "contains_pii_patterns",
                    "log_destination": "external_system",
                    "encryption_status": "unencrypted"
                },
                "actions": ["encrypt_logs", "alert_compliance_team", "remediate_exposure"],
                "severity": "CRITICAL"
            }
        ]