"""
Automated monitoring and alerting for input validation security
"""
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ValidationSecurityMonitor:
    """Monitor input validation for security incidents and patterns"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        
    def create_validation_metrics_dashboard(self):
        """Create CloudWatch dashboard for validation security metrics"""
        
        dashboard_config = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["HealthAI/Security", "PIIDetected", {"stat": "Sum"}],
                            [".", "PromptInjectionAttempts", {"stat": "Sum"}],
                            [".", "DangerousAdviceRequests", {"stat": "Sum"}],
                            [".", "ValidationFailures", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Security Validation Events",
                        "annotations": {
                            "horizontal": [
                                {"label": "Critical Alert Threshold", "value": 10}
                            ]
                        }
                    }
                },
                {
                    "type": "metric", 
                    "properties": {
                        "metrics": [
                            ["HealthAI/Security", "HighRiskQueries", {"stat": "Sum"}],
                            [".", "CriticalRiskQueries", {"stat": "Sum"}],
                            [".", "MedicalContextScore", {"stat": "Average"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Risk Assessment Metrics"
                    }
                },
                {
                    "type": "log",
                    "properties": {
                        "query": "SOURCE '/aws/ecs/healthai'\n| fields @timestamp, risk_level, violations, query_hash\n| filter event_type = \"INPUT_VALIDATION\"\n| filter risk_level in [\"HIGH\", \"CRITICAL\"]\n| stats count() by violations\n| sort count desc\n| limit 20",
                        "region": "us-east-1", 
                        "title": "Top Security Violations"
                    }
                }
            ]
        }
        
        return self.cloudwatch.put_dashboard(
            DashboardName='HealthAI-Input-Security-Monitoring',
            DashboardBody=json.dumps(dashboard_config)
        )
    
    def setup_security_alarms(self):
        """Set up CloudWatch alarms for security incidents"""
        
        # Critical: PII Detection Alarm
        self.cloudwatch.put_metric_alarm(
            AlarmName='HealthAI-PII-Detection-Critical',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='PIIDetected',
            Namespace='HealthAI/Security',
            Period=300,
            Statistic='Sum',
            Threshold=5.0,
            ActionsEnabled=True,
            AlarmActions=[
                'arn:aws:sns:us-east-1:123456789012:healthai-security-critical'
            ],
            AlarmDescription='CRITICAL: PII detected in medical queries - potential HIPAA violation',
            Unit='Count',
            TreatMissingData='notBreaching'
        )
        
        # High: Prompt Injection Attempts
        self.cloudwatch.put_metric_alarm(
            AlarmName='HealthAI-Prompt-Injection-Attempts',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=2,
            MetricName='PromptInjectionAttempts',
            Namespace='HealthAI/Security',
            Period=300,
            Statistic='Sum',
            Threshold=10.0,
            ActionsEnabled=True,
            AlarmActions=[
                'arn:aws:sns:us-east-1:123456789012:healthai-security-high'
            ],
            AlarmDescription='HIGH: Multiple prompt injection attempts detected'
        )
        
        # Medium: Unusual validation failure rate
        self.cloudwatch.put_metric_alarm(
            AlarmName='HealthAI-High-Validation-Failure-Rate',
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=3,
            MetricName='ValidationFailureRate',
            Namespace='HealthAI/Security',
            Period=600,
            Statistic='Average',
            Threshold=25.0,  # 25% failure rate
            ActionsEnabled=True,
            AlarmActions=[
                'arn:aws:sns:us-east-1:123456789012:healthai-security-medium'
            ],
            AlarmDescription='MEDIUM: High validation failure rate may indicate attack or system issue'
        )
    
    def generate_security_report(self, hours_back: int = 24) -> Dict:
        """Generate security report for validation events"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        try:
            # Query validation security metrics
            metrics_data = self.cloudwatch.get_metric_statistics(
                Namespace='HealthAI/Security',
                MetricName='PIIDetected',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            pii_incidents = sum(point['Sum'] for point in metrics_data.get('Datapoints', []))
            
            # Get injection attempt metrics
            injection_data = self.cloudwatch.get_metric_statistics(
                Namespace='HealthAI/Security',
                MetricName='PromptInjectionAttempts',
                Dimensions=[],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            injection_attempts = sum(point['Sum'] for point in injection_data.get('Datapoints', []))
            
            return {
                "period": f"Last {hours_back} hours",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "security_summary": {
                    "pii_incidents": int(pii_incidents),
                    "prompt_injection_attempts": int(injection_attempts),
                    "status": self._assess_security_status(pii_incidents, injection_attempts),
                    "recommendations": self._generate_recommendations(pii_incidents, injection_attempts)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {"error": "Failed to generate security report", "details": str(e)}
    
    def _assess_security_status(self, pii_incidents: float, injection_attempts: float) -> str:
        """Assess overall security status"""
        if pii_incidents > 5:
            return "CRITICAL - Immediate action required"
        elif pii_incidents > 0 or injection_attempts > 20:
            return "HIGH - Investigation needed"
        elif injection_attempts > 5:
            return "MEDIUM - Monitor closely"
        else:
            return "NORMAL - No immediate concerns"
    
    def _generate_recommendations(self, pii_incidents: float, injection_attempts: float) -> List[str]:
        """Generate security recommendations based on metrics"""
        recommendations = []
        
        if pii_incidents > 0:
            recommendations.extend([
                "Review HIPAA compliance procedures",
                "Conduct staff training on PII handling",
                "Audit data handling processes"
            ])
        
        if injection_attempts > 10:
            recommendations.extend([
                "Review rate limiting configuration",
                "Consider IP blocking for repeated offenders",
                "Update prompt injection detection patterns"
            ])
        
        if not recommendations:
            recommendations.append("Continue monitoring - system is secure")
        
        return recommendations

# Automation script for daily security checks
def automated_security_check():
    """Automated daily security validation check"""
    
    monitor = ValidationSecurityMonitor()
    
    try:
        # Generate daily report
        report = monitor.generate_security_report(hours_back=24)
        
        # Log report for audit trail
        logger.info(f"Daily security report: {json.dumps(report)}")
        
        # Send alert if critical issues found
        if "CRITICAL" in report.get("security_summary", {}).get("status", ""):
            # Send immediate notification
            sns = boto3.client('sns')
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789012:healthai-security-critical',
                Message=f"CRITICAL SECURITY ALERT: {json.dumps(report, indent=2)}",
                Subject="HealthAI - Critical Security Issue Detected"
            )
        
        return report
        
    except Exception as e:
        logger.error(f"Automated security check failed: {e}")
        return {"error": "Security check failed", "details": str(e)}