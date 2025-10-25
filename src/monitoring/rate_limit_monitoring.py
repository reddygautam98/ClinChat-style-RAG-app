"""
CloudWatch monitoring for rate limiting in healthcare API
"""
import boto3
import json
from datetime import datetime, timedelta

def create_rate_limit_dashboard():
    """Create CloudWatch dashboard for rate limiting monitoring"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["HealthAI/RateLimit", "RequestsBlocked", {"stat": "Sum"}],
                        [".", "RequestsAllowed", {"stat": "Sum"}],
                        [".", "BurstLimitViolations", {"stat": "Sum"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Rate Limiting Overview",
                    "annotations": {
                        "horizontal": [
                            {"label": "Critical Threshold", "value": 1000}
                        ]
                    }
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["HealthAI/RateLimit", "MedicalQueryRate", {"stat": "Average"}],
                        [".", "DocumentUploadRate", {"stat": "Average"}],
                        [".", "AdminOperationRate", {"stat": "Average"}]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "Endpoint-Specific Rates"
                }
            },
            {
                "type": "log",
                "properties": {
                    "query": "SOURCE '/aws/ecs/healthai'\n| fields @timestamp, client_id, endpoint, event_type\n| filter event_type = \"RATE_LIMIT_VIOLATION\"\n| stats count() by endpoint\n| sort count desc",
                    "region": "us-east-1",
                    "title": "Rate Limit Violations by Endpoint"
                }
            }
        ]
    }
    
    return cloudwatch.put_dashboard(
        DashboardName='HealthAI-RateLimit-Monitoring',
        DashboardBody=json.dumps(dashboard_body)
    )

def setup_rate_limit_alarms():
    """Set up CloudWatch alarms for rate limiting"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    # Alarm for excessive rate limit violations
    cloudwatch.put_metric_alarm(
        AlarmName='HealthAI-ExcessiveRateLimitViolations',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='RequestsBlocked',
        Namespace='HealthAI/RateLimit',
        Period=300,
        Statistic='Sum',
        Threshold=100.0,
        ActionsEnabled=True,
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:healthai-security-alerts'
        ],
        AlarmDescription='Alert when rate limiting blocks exceed threshold',
        Unit='Count'
    )
    
    # Alarm for Redis connectivity issues
    cloudwatch.put_metric_alarm(
        AlarmName='HealthAI-Redis-ConnectionFailures',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='RedisErrors',
        Namespace='HealthAI/RateLimit',
        Period=60,
        Statistic='Sum',
        Threshold=5.0,
        ActionsEnabled=True,
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:healthai-infrastructure-alerts'
        ],
        AlarmDescription='Alert when Redis connection failures occur'
    )