"""
Automated API Key Rotation for AI Services (Gemini/Groq)
AWS Secrets Manager integration with Lambda rotation function
"""
import boto3
import json
import logging
import os
from typing import Dict, Any
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIServiceKeyRotator:
    """Automated rotation for AI service API keys"""
    
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager')
        self.sns_client = boto3.client('sns')
        self.cloudwatch = boto3.client('cloudwatch')
        
        # Configuration
        self.rotation_schedule = {
            'gemini_api_key': 30,  # days
            'groq_api_key': 30,    # days  
            'openai_api_key': 30   # days (if used)
        }
        
        self.notification_topic = 'arn:aws:sns:us-east-1:123456789012:healthai-key-rotation'
    
    def rotate_gemini_key(self, secret_name: str) -> Dict[str, Any]:
        """Rotate Google Gemini API key"""
        
        try:
            # Get current secret
            current_secret = self.secrets_client.get_secret_value(SecretId=secret_name)
            current_key_data = json.loads(current_secret['SecretString'])
            
            # Generate new API key (this would call Google's API key management)
            new_key = self._generate_new_gemini_key()
            
            if not new_key:
                raise Exception("Failed to generate new Gemini API key")
            
            # Test new key before rotation
            if not self._test_gemini_key(new_key):
                raise Exception("New Gemini API key validation failed")
            
            # Prepare new secret version
            new_secret_data = {
                **current_key_data,
                'api_key': new_key,
                'rotation_date': datetime.utcnow().isoformat(),
                'previous_key': current_key_data.get('api_key'),  # Keep for rollback
                'key_status': 'active'
            }
            
            # Update secret in AWS Secrets Manager
            response = self.secrets_client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(new_secret_data)
            )
            
            # Schedule old key deactivation (grace period)
            self._schedule_key_deactivation(
                service='gemini',
                old_key=current_key_data.get('api_key'),
                delay_hours=24  # 24-hour grace period
            )
            
            # Log successful rotation
            self._log_rotation_event('GEMINI', secret_name, True)
            
            # Send notification
            self._send_rotation_notification('GEMINI', secret_name, True)
            
            return {
                'status': 'success',
                'service': 'gemini',
                'secret_name': secret_name,
                'rotation_time': datetime.utcnow().isoformat(),
                'version_id': response['VersionId']
            }
            
        except Exception as e:
            logger.error(f"Gemini key rotation failed: {str(e)}")
            self._log_rotation_event('GEMINI', secret_name, False, str(e))
            self._send_rotation_notification('GEMINI', secret_name, False, str(e))
            
            return {
                'status': 'failed',
                'service': 'gemini',
                'secret_name': secret_name,
                'error': str(e),
                'rotation_time': datetime.utcnow().isoformat()
            }
    
    def rotate_groq_key(self, secret_name: str) -> Dict[str, Any]:
        """Rotate Groq API key"""
        
        try:
            # Get current secret
            current_secret = self.secrets_client.get_secret_value(SecretId=secret_name)
            current_key_data = json.loads(current_secret['SecretString'])
            
            # Generate new API key (this would call Groq's API key management)
            new_key = self._generate_new_groq_key()
            
            if not new_key:
                raise Exception("Failed to generate new Groq API key")
            
            # Test new key
            if not self._test_groq_key(new_key):
                raise Exception("New Groq API key validation failed")
            
            # Update secret
            new_secret_data = {
                **current_key_data,
                'api_key': new_key,
                'rotation_date': datetime.utcnow().isoformat(),
                'previous_key': current_key_data.get('api_key'),
                'key_status': 'active'
            }
            
            response = self.secrets_client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(new_secret_data)
            )
            
            # Schedule old key deactivation
            self._schedule_key_deactivation(
                service='groq',
                old_key=current_key_data.get('api_key'),
                delay_hours=24
            )
            
            self._log_rotation_event('GROQ', secret_name, True)
            self._send_rotation_notification('GROQ', secret_name, True)
            
            return {
                'status': 'success',
                'service': 'groq',
                'secret_name': secret_name,
                'rotation_time': datetime.utcnow().isoformat(),
                'version_id': response['VersionId']
            }
            
        except Exception as e:
            logger.error(f"Groq key rotation failed: {str(e)}")
            self._log_rotation_event('GROQ', secret_name, False, str(e))
            self._send_rotation_notification('GROQ', secret_name, False, str(e))
            
            return {
                'status': 'failed',
                'service': 'groq',
                'secret_name': secret_name,
                'error': str(e),
                'rotation_time': datetime.utcnow().isoformat()
            }
    
    def _generate_new_gemini_key(self) -> str:
        """Generate new Google Gemini API key"""
        
        # This would integrate with Google Cloud's API Key Management
        # For now, returning placeholder - implement actual key generation
        
        try:
            # Example: Call Google Cloud API Key service
            # response = google_client.create_api_key(...)
            
            # Placeholder for demo
            new_key = f"gemini_key_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            logger.info("New Gemini API key generated successfully")
            return new_key
            
        except Exception as e:
            logger.error(f"Failed to generate Gemini key: {e}")
            return None
    
    def _generate_new_groq_key(self) -> str:
        """Generate new Groq API key"""
        
        # This would integrate with Groq's API Key Management
        try:
            # Example: Call Groq API Key service
            # response = groq_client.create_api_key(...)
            
            # Placeholder for demo
            new_key = f"groq_key_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            logger.info("New Groq API key generated successfully")
            return new_key
            
        except Exception as e:
            logger.error(f"Failed to generate Groq key: {e}")
            return None
    
    def _test_gemini_key(self, api_key: str) -> bool:
        """Test if new Gemini API key is working"""
        
        try:
            # Test with a simple API call
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Make a minimal API call to verify key works
            response = requests.get(
                'https://generativelanguage.googleapis.com/v1/models',
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Gemini key test failed: {e}")
            return False
    
    def _test_groq_key(self, api_key: str) -> bool:
        """Test if new Groq API key is working"""
        
        try:
            # Test with a simple API call
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://api.groq.com/openai/v1/models',
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Groq key test failed: {e}")
            return False
    
    def _schedule_key_deactivation(self, service: str, old_key: str, delay_hours: int):
        """Schedule deactivation of old API key after grace period"""
        
        # Create CloudWatch event rule for delayed deactivation
        events_client = boto3.client('events')
        
        # Schedule Lambda function to deactivate old key
        rule_name = f"deactivate-{service}-key-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate activation time
        activation_time = datetime.utcnow() + timedelta(hours=delay_hours)
        
        try:
            # Create scheduled event
            events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=f"at({activation_time.strftime('%Y-%m-%dT%H:%M:%S')})",
                Description=f"Deactivate old {service} API key after grace period",
                State='ENABLED'
            )
            
            # Add target to invoke deactivation function
            events_client.put_targets(
                Rule=rule_name,
                Targets=[{
                    'Id': '1',
                    'Arn': f'arn:aws:lambda:us-east-1:123456789012:function:deactivate-{service}-key',
                    'Input': json.dumps({
                        'service': service,
                        'old_key_hash': self._hash_key(old_key),  # Hash for security
                        'deactivation_reason': 'rotation_grace_period_expired'
                    })
                }]
            )
            
            logger.info(f"Scheduled {service} key deactivation in {delay_hours} hours")
            
        except Exception as e:
            logger.error(f"Failed to schedule key deactivation: {e}")
    
    def _hash_key(self, key: str) -> str:
        """Hash API key for secure logging"""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def _log_rotation_event(self, service: str, secret_name: str, success: bool, error: str = None):
        """Log rotation event for audit purposes"""
        
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'API_KEY_ROTATION',
            'service': service,
            'secret_name': secret_name,
            'success': success,
            'error': error,
            'compliance_framework': 'SOC2_HIPAA'
        }
        
        logger.info(f"API Key Rotation Event: {json.dumps(event_data)}")
        
        # Send to CloudWatch for monitoring
        try:
            self.cloudwatch.put_metric_data(
                Namespace='HealthAI/Security',
                MetricData=[
                    {
                        'MetricName': 'APIKeyRotationEvents',
                        'Dimensions': [
                            {'Name': 'Service', 'Value': service},
                            {'Name': 'Success', 'Value': str(success)}
                        ],
                        'Value': 1,
                        'Unit': 'Count'
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to send rotation metrics: {e}")
    
    def _send_rotation_notification(self, service: str, secret_name: str, success: bool, error: str = None):
        """Send rotation notification to security team"""
        
        if success:
            message = f"✅ {service} API key rotation completed successfully\nSecret: {secret_name}\nTime: {datetime.utcnow().isoformat()}"
            subject = f"HealthAI - {service} API Key Rotated Successfully"
        else:
            message = f"❌ {service} API key rotation FAILED\nSecret: {secret_name}\nError: {error}\nTime: {datetime.utcnow().isoformat()}\n\nImmediate action required!"
            subject = f"URGENT - HealthAI {service} API Key Rotation Failed"
        
        try:
            self.sns_client.publish(
                TopicArn=self.notification_topic,
                Message=message,
                Subject=subject
            )
        except Exception as e:
            logger.error(f"Failed to send rotation notification: {e}")

# Lambda handler for automated rotation
def lambda_handler(event, context):
    """AWS Lambda handler for automated API key rotation"""
    
    rotator = AIServiceKeyRotator()
    results = []
    
    try:
        # Get secrets to rotate from event or environment
        secrets_to_rotate = event.get('secrets', [
            'prod/healthai/gemini-api-key',
            'prod/healthai/groq-api-key'
        ])
        
        for secret_name in secrets_to_rotate:
            if 'gemini' in secret_name.lower():
                result = rotator.rotate_gemini_key(secret_name)
            elif 'groq' in secret_name.lower():
                result = rotator.rotate_groq_key(secret_name)
            else:
                result = {
                    'status': 'skipped',
                    'secret_name': secret_name,
                    'reason': 'Unknown service type'
                }
            
            results.append(result)
        
        # Summary
        successful_rotations = sum(1 for r in results if r['status'] == 'success')
        failed_rotations = sum(1 for r in results if r['status'] == 'failed')
        
        return {
            'statusCode': 200 if failed_rotations == 0 else 500,
            'body': json.dumps({
                'message': f'Rotation completed: {successful_rotations} successful, {failed_rotations} failed',
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda rotation handler failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Rotation process failed',
                'details': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }