"""
API Key Rotation Monitoring and Automation Scripts
"""
import boto3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def create_key_rotation_monitoring():
    """Create comprehensive monitoring for API key rotation"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    # Dashboard configuration
    dashboard_config = {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["HealthAI/Security", "APIKeyRotationEvents", "Service", "GEMINI", "Success", "True"],
                        [".", ".", ".", "GROQ", ".", "."],
                        [".", ".", ".", "GEMINI", ".", "False"],  
                        [".", ".", ".", "GROQ", ".", "False"]
                    ],
                    "period": 86400,  # Daily
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "API Key Rotation Success/Failure Rate"
                }
            },
            {
                "type": "log",
                "properties": {
                    "query": "SOURCE '/aws/lambda/healthai-key-rotation-production'\n| fields @timestamp, service, success, error\n| filter event_type = \"API_KEY_ROTATION\"\n| stats count() by service, success\n| sort @timestamp desc",
                    "region": "us-east-1",
                    "title": "Recent Key Rotation Events"
                }
            }
        ]
    }
    
    try:
        response = cloudwatch.put_dashboard(
            DashboardName='HealthAI-API-Key-Rotation-Monitor',
            DashboardBody=json.dumps(dashboard_config)
        )
        print("✅ Key rotation monitoring dashboard created")
        return response
    except Exception as e:
        print(f"❌ Failed to create dashboard: {e}")
        return None

def deploy_key_rotation_infrastructure():
    """Deploy key rotation CloudFormation stack"""
    
    cloudformation = boto3.client('cloudformation')
    
    try:
        # Read the CloudFormation template
        with open('infrastructure/key-rotation-stack.yaml', 'r') as f:
            template_body = f.read()
        
        # Deploy stack
        response = cloudformation.create_stack(
            StackName='healthai-key-rotation-production',
            TemplateBody=template_body,
            Parameters=[
                {
                    'ParameterKey': 'Environment',
                    'ParameterValue': 'production'
                },
                {
                    'ParameterKey': 'NotificationEmail',
                    'ParameterValue': 'security@healthai.com'  # Update with actual email
                }
            ],
            Capabilities=['CAPABILITY_NAMED_IAM'],
            Tags=[
                {'Key': 'Project', 'Value': 'HealthAI'},
                {'Key': 'Purpose', 'Value': 'API-Key-Security'},
                {'Key': 'Environment', 'Value': 'production'}
            ]
        )
        
        print("✅ Key rotation infrastructure deployment started")
        print(f"Stack ID: {response['StackId']}")
        
        return response
        
    except Exception as e:
        print(f"❌ Failed to deploy infrastructure: {e}")
        return None

def test_key_rotation():
    """Test API key rotation functionality"""
    
    lambda_client = boto3.client('lambda')
    
    test_payload = {
        "test_mode": True,
        "secrets": [
            "prod/healthai/gemini-api-key-production",
            "prod/healthai/groq-api-key-production"
        ],
        "environment": "production",
        "triggered_by": "manual_test"
    }
    
    try:
        # Invoke rotation function
        response = lambda_client.invoke(
            FunctionName='healthai-key-rotation-production',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        print("✅ Key rotation test completed")
        print(f"Status: {result.get('statusCode')}")
        print(f"Results: {json.dumps(result, indent=2)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Key rotation test failed: {e}")
        return None

def check_key_ages():
    """Check age of current API keys and alert if rotation needed"""
    
    secrets_client = boto3.client('secretsmanager')
    
    secrets_to_check = [
        'prod/healthai/gemini-api-key-production',
        'prod/healthai/groq-api-key-production'
    ]
    
    alerts = []
    
    for secret_name in secrets_to_check:
        try:
            # Get secret metadata
            response = secrets_client.describe_secret(SecretId=secret_name)
            
            last_changed = response.get('LastChangedDate')
            if last_changed:
                age_days = (datetime.now(last_changed.tzinfo) - last_changed).days
                
                # Alert thresholds
                if age_days > 35:  # Past due for rotation
                    alerts.append({
                        'secret': secret_name,
                        'age_days': age_days,
                        'status': 'OVERDUE',
                        'action': 'Immediate rotation required'
                    })
                elif age_days > 28:  # Due for rotation soon
                    alerts.append({
                        'secret': secret_name,
                        'age_days': age_days,
                        'status': 'DUE_SOON',
                        'action': 'Schedule rotation within 2 days'
                    })
                else:
                    print(f"✅ {secret_name}: {age_days} days old (OK)")
            
        except Exception as e:
            alerts.append({
                'secret': secret_name,
                'error': str(e),
                'status': 'CHECK_FAILED',
                'action': 'Investigate secret access issue'
            })
    
    # Send alerts if needed
    if alerts:
        send_key_age_alerts(alerts)
    
    return alerts

def send_key_age_alerts(alerts):
    """Send alerts for keys that need rotation"""
    
    sns = boto3.client('sns')
    
    alert_message = "🔑 HealthAI API Key Rotation Alert\n\n"
    
    for alert in alerts:
        alert_message += f"Secret: {alert['secret']}\n"
        alert_message += f"Status: {alert['status']}\n"
        
        if 'age_days' in alert:
            alert_message += f"Age: {alert['age_days']} days\n"
        if 'error' in alert:
            alert_message += f"Error: {alert['error']}\n"
            
        alert_message += f"Action: {alert['action']}\n\n"
    
    try:
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:healthai-key-rotation-notifications-production',
            Message=alert_message,
            Subject='HealthAI - API Key Rotation Alert'
        )
        print("✅ Key age alerts sent")
    except Exception as e:
        print(f"❌ Failed to send alerts: {e}")

# CLI functions for manual operations
def manual_rotate_key(service_name):
    """Manually trigger key rotation for specific service"""
    
    lambda_client = boto3.client('lambda')
    
    if service_name.lower() == 'gemini':
        secret_name = 'prod/healthai/gemini-api-key-production'
    elif service_name.lower() == 'groq':
        secret_name = 'prod/healthai/groq-api-key-production'
    else:
        print(f"❌ Unknown service: {service_name}")
        return None
    
    payload = {
        "manual_rotation": True,
        "secrets": [secret_name],
        "environment": "production",
        "triggered_by": f"manual_{service_name}",
        "emergency": False
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='healthai-manual-key-rotation-production',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            print(f"✅ {service_name} key rotation completed successfully")
        else:
            print(f"❌ {service_name} key rotation failed")
            
        print(f"Details: {json.dumps(result, indent=2)}")
        return result
        
    except Exception as e:
        print(f"❌ Manual rotation failed: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python key_rotation_monitor.py <command>")
        print("Commands: deploy, monitor, test, check-ages, rotate <service>")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "deploy":
        deploy_key_rotation_infrastructure()
    elif command == "monitor":
        create_key_rotation_monitoring()
    elif command == "test":
        test_key_rotation()
    elif command == "check-ages":
        alerts = check_key_ages()
        if alerts:
            print(f"\n⚠️  Found {len(alerts)} key rotation alerts")
    elif command == "rotate" and len(sys.argv) > 2:
        service = sys.argv[2]
        manual_rotate_key(service)
    else:
        print("Invalid command. Use: deploy, monitor, test, check-ages, or rotate <service>")