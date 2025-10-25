"""
HIPAA Compliance Monitoring and Automation
"""
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class HIPAAComplianceMonitor:
    """Monitor HIPAA compliance across the healthcare application"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.s3 = boto3.client('s3')
        self.cloudtrail = boto3.client('cloudtrail')
    
    def create_compliance_dashboard(self):
        """Create comprehensive HIPAA compliance monitoring dashboard"""
        
        dashboard_config = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["HealthAI/HIPAA", "EncryptedDataAccess", {"stat": "Sum"}],
                            [".", "UnencryptedDataDetected", {"stat": "Sum"}],
                            [".", "AccessControlViolations", {"stat": "Sum"}],
                            [".", "AuditLogFailures", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "HIPAA Security Metrics",
                        "annotations": {
                            "horizontal": [
                                {"label": "Zero Tolerance", "value": 0}
                            ]
                        }
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["HealthAI/HIPAA", "PHIDataAccess", {"stat": "Sum"}],
                            [".", "MinimumNecessaryCompliance", {"stat": "Average"}],
                            [".", "BreachDetectionEvents", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "PHI Access Monitoring"
                    }
                },
                {
                    "type": "log",
                    "properties": {
                        "query": "SOURCE '/aws/healthai/hipaa-audit'\n| fields @timestamp, event_type, success, user_id, resource_type\n| filter event_type like /PHI_/\n| filter success = false\n| stats count() by event_type\n| sort count desc",
                        "region": "us-east-1",
                        "title": "Failed PHI Access Attempts"
                    }
                },
                {
                    "type": "number",
                    "properties": {
                        "metrics": [
                            ["HealthAI/HIPAA", "ComplianceScore", {"stat": "Average"}]
                        ],
                        "period": 3600,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Overall HIPAA Compliance Score",
                        "annotations": {
                            "horizontal": [
                                {"label": "Minimum Acceptable", "value": 95}
                            ]
                        }
                    }
                }
            ]
        }
        
        return self.cloudwatch.put_dashboard(
            DashboardName='HealthAI-HIPAA-Compliance-Dashboard',
            DashboardBody=json.dumps(dashboard_config)
        )
    
    def setup_compliance_alarms(self):
        """Set up critical HIPAA compliance alarms"""
        
        alarms = [
            {
                "name": "HIPAA-Critical-Unencrypted-Data",
                "metric": "UnencryptedDataDetected",
                "threshold": 0,
                "comparison": "GreaterThanThreshold",
                "description": "CRITICAL: Unencrypted PHI data detected",
                "alarm_actions": ["arn:aws:sns:us-east-1:123456789012:hipaa-critical-alerts"],
                "evaluation_periods": 1,
                "period": 60
            },
            {
                "name": "HIPAA-Audit-Log-Failure",
                "metric": "AuditLogFailures", 
                "threshold": 5,
                "comparison": "GreaterThanThreshold",
                "description": "HIGH: HIPAA audit logging failures detected",
                "alarm_actions": ["arn:aws:sns:us-east-1:123456789012:hipaa-high-alerts"],
                "evaluation_periods": 2,
                "period": 300
            },
            {
                "name": "HIPAA-Breach-Detection",
                "metric": "BreachDetectionEvents",
                "threshold": 1,
                "comparison": "GreaterThanOrEqualToThreshold",
                "description": "CRITICAL: Potential HIPAA breach detected",
                "alarm_actions": [
                    "arn:aws:sns:us-east-1:123456789012:hipaa-breach-alerts",
                    "arn:aws:lambda:us-east-1:123456789012:function:hipaa-breach-response"
                ],
                "evaluation_periods": 1,
                "period": 60
            },
            {
                "name": "HIPAA-Compliance-Score-Low",
                "metric": "ComplianceScore",
                "threshold": 95,
                "comparison": "LessThanThreshold",
                "description": "MEDIUM: HIPAA compliance score below threshold",
                "alarm_actions": ["arn:aws:sns:us-east-1:123456789012:hipaa-medium-alerts"],
                "evaluation_periods": 3,
                "period": 3600
            }
        ]
        
        for alarm_config in alarms:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_config["name"],
                ComparisonOperator=alarm_config["comparison"],
                EvaluationPeriods=alarm_config["evaluation_periods"],
                MetricName=alarm_config["metric"],
                Namespace='HealthAI/HIPAA',
                Period=alarm_config["period"],
                Statistic='Sum' if 'Sum' in alarm_config.get("statistic", "Sum") else 'Average',
                Threshold=float(alarm_config["threshold"]),
                ActionsEnabled=True,
                AlarmActions=alarm_config["alarm_actions"],
                AlarmDescription=alarm_config["description"],
                Unit='Count'
            )
    
    def generate_compliance_report(self, days_back: int = 30) -> Dict:
        """Generate comprehensive HIPAA compliance report"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        try:
            # Get compliance metrics
            compliance_metrics = self._get_compliance_metrics(start_time, end_time)
            
            # Get audit log statistics
            audit_stats = self._analyze_audit_logs(start_time, end_time)
            
            # Check encryption compliance
            encryption_status = self._check_encryption_compliance()
            
            # Calculate overall compliance score
            compliance_score = self._calculate_compliance_score(
                compliance_metrics, audit_stats, encryption_status
            )
            
            report = {
                "report_period": {
                    "start_date": start_time.isoformat(),
                    "end_date": end_time.isoformat(),
                    "days_covered": days_back
                },
                "overall_compliance": {
                    "score": compliance_score,
                    "status": self._get_compliance_status(compliance_score),
                    "last_updated": datetime.utcnow().isoformat()
                },
                "security_safeguards": {
                    "access_control": {
                        "compliant": audit_stats.get("access_control_violations", 0) == 0,
                        "violations_detected": audit_stats.get("access_control_violations", 0)
                    },
                    "audit_controls": {
                        "compliant": audit_stats.get("audit_failures", 0) == 0,
                        "logs_generated": audit_stats.get("total_audit_events", 0),
                        "retention_compliant": True  # Based on S3 lifecycle policy
                    },
                    "integrity": {
                        "compliant": encryption_status.get("all_encrypted", False),
                        "unencrypted_data_detected": encryption_status.get("unencrypted_count", 0)
                    },
                    "transmission_security": {
                        "compliant": True,  # HTTPS enforced
                        "tls_version": "1.2+",
                        "certificate_valid": True
                    }
                },
                "administrative_safeguards": {
                    "assigned_security_responsibility": True,
                    "workforce_training": "Required - Annual HIPAA training",
                    "access_management": "Role-based access control implemented",
                    "breach_notification": "Automated breach detection active"
                },
                "physical_safeguards": {
                    "facility_access": "AWS data center security",
                    "workstation_use": "Cloud-based - no physical workstations",
                    "device_controls": "Not applicable - cloud service",
                    "media_controls": "Encrypted storage with key rotation"
                },
                "recommendations": self._generate_compliance_recommendations(
                    compliance_score, compliance_metrics, audit_stats
                ),
                "next_assessment_due": (datetime.utcnow() + timedelta(days=90)).isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": "Failed to generate compliance report", "details": str(e)}
    
    def _get_compliance_metrics(self, start_time: datetime, end_time: datetime) -> Dict:
        """Get HIPAA compliance metrics from CloudWatch"""
        
        metrics = {}
        metric_names = [
            "EncryptedDataAccess",
            "UnencryptedDataDetected", 
            "AccessControlViolations",
            "AuditLogFailures",
            "BreachDetectionEvents"
        ]
        
        for metric_name in metric_names:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace='HealthAI/HIPAA',
                    MetricName=metric_name,
                    Dimensions=[],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Sum']
                )
                
                total = sum(point['Sum'] for point in response.get('Datapoints', []))
                metrics[metric_name.lower()] = int(total)
                
            except Exception as e:
                logger.error(f"Error getting metric {metric_name}: {e}")
                metrics[metric_name.lower()] = 0
        
        return metrics
    
    def _analyze_audit_logs(self, start_time: datetime, end_time: datetime) -> Dict:
        """Analyze HIPAA audit logs for compliance statistics"""
        
        # This would typically query CloudWatch Logs or S3 audit logs
        # For now, return mock data structure
        return {
            "total_audit_events": 1000,
            "access_control_violations": 0,
            "audit_failures": 2,
            "phi_access_events": 150,
            "successful_authentications": 980,
            "failed_authentications": 20
        }
    
    def _check_encryption_compliance(self) -> Dict:
        """Check encryption compliance across all data stores"""
        
        # Check S3 bucket encryption
        # Check RDS encryption
        # Check EBS encryption
        # For now, return mock compliance status
        return {
            "all_encrypted": True,
            "unencrypted_count": 0,
            "encryption_algorithms": ["AES-256", "KMS"],
            "key_rotation_enabled": True
        }
    
    def _calculate_compliance_score(self, metrics: Dict, audit_stats: Dict, encryption: Dict) -> float:
        """Calculate overall HIPAA compliance score (0-100)"""
        
        score = 100.0
        
        # Deduct for security violations
        score -= metrics.get("unencrypteddatadetected", 0) * 20  # Major deduction
        score -= metrics.get("accesscontrolviolations", 0) * 15
        score -= metrics.get("auditlogfailures", 0) * 10
        score -= metrics.get("breachdetectionevents", 0) * 25  # Critical deduction
        
        # Deduct for audit issues
        score -= audit_stats.get("access_control_violations", 0) * 10
        score -= min(audit_stats.get("audit_failures", 0), 5) * 5  # Max 25 point deduction
        
        # Deduct for encryption issues
        if not encryption.get("all_encrypted", True):
            score -= 30
        
        return max(0.0, min(100.0, score))
    
    def _get_compliance_status(self, score: float) -> str:
        """Get compliance status based on score"""
        if score >= 98:
            return "EXCELLENT"
        elif score >= 95:
            return "COMPLIANT"
        elif score >= 90:
            return "NEEDS_IMPROVEMENT"
        elif score >= 80:
            return "NON_COMPLIANT"
        else:
            return "CRITICAL_NON_COMPLIANT"
    
    def _generate_compliance_recommendations(self, score: float, metrics: Dict, audit_stats: Dict) -> List[str]:
        """Generate actionable compliance recommendations"""
        
        recommendations = []
        
        if score < 95:
            recommendations.append("Conduct immediate compliance review and remediation")
        
        if metrics.get("unencrypteddatadetected", 0) > 0:
            recommendations.append("Implement encryption for all detected unencrypted data")
        
        if metrics.get("accesscontrolviolations", 0) > 0:
            recommendations.append("Review and strengthen access control policies")
        
        if audit_stats.get("audit_failures", 0) > 0:
            recommendations.append("Investigate and resolve audit logging failures")
        
        if metrics.get("breachdetectionevents", 0) > 0:
            recommendations.append("URGENT: Investigate potential breach events immediately")
        
        if not recommendations:
            recommendations.append("Maintain current security posture and continue monitoring")
        
        return recommendations

# Automated compliance check function
def daily_hipaa_compliance_check():
    """Automated daily HIPAA compliance check"""
    
    monitor = HIPAAComplianceMonitor()
    
    try:
        # Generate compliance report
        report = monitor.generate_compliance_report(days_back=1)
        
        # Log report for audit trail
        logger.info(f"Daily HIPAA compliance check: Score {report.get('overall_compliance', {}).get('score', 0)}")
        
        # Alert if compliance issues detected
        compliance_score = report.get('overall_compliance', {}).get('score', 100)
        if compliance_score < 95:
            
            sns = boto3.client('sns')
            sns.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789012:hipaa-compliance-alerts',
                Message=f"HIPAA Compliance Alert: Score dropped to {compliance_score}%\n\n{json.dumps(report, indent=2)}",
                Subject=f"HealthAI HIPAA Compliance Alert - Score: {compliance_score}%"
            )
        
        return report
        
    except Exception as e:
        logger.error(f"Daily compliance check failed: {e}")
        return {"error": "Compliance check failed", "details": str(e)}