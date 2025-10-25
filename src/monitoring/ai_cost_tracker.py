"""
AI Model Cost Tracking and Optimization System
Real-time cost monitoring for Gemini, Groq, and other AI services
"""
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class AIModelUsage:
    """Track AI model usage and costs"""
    timestamp: str
    service: str  # gemini, groq, openai
    model: str    # specific model name
    tokens_input: int
    tokens_output: int
    cost_input: Decimal
    cost_output: Decimal
    total_cost: Decimal
    query_type: str  # medical, admin, test
    user_hash: str   # anonymized user identifier
    session_id: str
    response_time_ms: int
    success: bool
    error_message: Optional[str] = None

class AIModelCostTracker:
    """Real-time AI model cost tracking and optimization"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.dynamodb = boto3.resource('dynamodb')
        self.sns = boto3.client('sns')
        
        # Cost per token for different models (update with current pricing)
        self.pricing = {
            'gemini-1.5-pro': {
                'input_per_1k_tokens': Decimal('0.00125'),   # $1.25 per 1M tokens
                'output_per_1k_tokens': Decimal('0.005')     # $5.00 per 1M tokens
            },
            'gemini-1.5-flash': {
                'input_per_1k_tokens': Decimal('0.000075'),  # $0.075 per 1M tokens
                'output_per_1k_tokens': Decimal('0.0003')    # $0.30 per 1M tokens
            },
            'groq-llama3-70b': {
                'input_per_1k_tokens': Decimal('0.00059'),   # $0.59 per 1M tokens
                'output_per_1k_tokens': Decimal('0.00079')   # $0.79 per 1M tokens
            },
            'groq-mixtral-8x7b': {
                'input_per_1k_tokens': Decimal('0.00024'),   # $0.24 per 1M tokens
                'output_per_1k_tokens': Decimal('0.00024')   # $0.24 per 1M tokens
            }
        }
        
        # Budget thresholds
        self.budget_thresholds = {
            'daily': Decimal('100.00'),     # $100/day
            'weekly': Decimal('500.00'),    # $500/week  
            'monthly': Decimal('2000.00')   # $2000/month
        }
        
        # Initialize DynamoDB table for usage tracking
        self.usage_table_name = 'healthai-ai-usage-tracking'
        self.cost_table_name = 'healthai-ai-cost-summary'
    
    def track_ai_usage(self, 
                      service: str,
                      model: str, 
                      tokens_input: int,
                      tokens_output: int,
                      query_type: str,
                      user_id: str,
                      session_id: str,
                      response_time_ms: int,
                      success: bool,
                      error_message: Optional[str] = None) -> AIModelUsage:
        """Track AI model usage and calculate costs"""
        
        try:
            # Calculate costs
            model_key = f"{service}-{model}"
            pricing_info = self.pricing.get(model_key, {
                'input_per_1k_tokens': Decimal('0.002'),  # Default pricing
                'output_per_1k_tokens': Decimal('0.002')
            })
            
            cost_input = (Decimal(tokens_input) / 1000) * pricing_info['input_per_1k_tokens']
            cost_output = (Decimal(tokens_output) / 1000) * pricing_info['output_per_1k_tokens']
            total_cost = cost_input + cost_output
            
            # Create usage record
            usage_record = AIModelUsage(
                timestamp=datetime.utcnow().isoformat() + 'Z',
                service=service,
                model=model,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_input=cost_input,
                cost_output=cost_output,
                total_cost=total_cost,
                query_type=query_type,
                user_hash=self._hash_user_id(user_id),
                session_id=session_id,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message
            )
            
            # Store in DynamoDB
            self._store_usage_record(usage_record)
            
            # Send metrics to CloudWatch
            self._send_usage_metrics(usage_record)
            
            # Check budget thresholds
            self._check_budget_thresholds(total_cost)
            
            # Log for audit
            logger.info(f"AI Usage tracked: {service}/{model} - ${float(total_cost):.4f}")
            
            return usage_record
            
        except Exception as e:
            logger.error(f"Failed to track AI usage: {e}")
            raise
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy compliance"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _store_usage_record(self, usage_record: AIModelUsage):
        """Store usage record in DynamoDB"""
        
        try:
            table = self.dynamodb.Table(self.usage_table_name)
            
            # Convert Decimal to string for DynamoDB compatibility
            record_dict = asdict(usage_record)
            record_dict['cost_input'] = str(record_dict['cost_input'])
            record_dict['cost_output'] = str(record_dict['cost_output'])
            record_dict['total_cost'] = str(record_dict['total_cost'])
            
            # Add partition key for efficient querying
            record_dict['partition_key'] = f"{usage_record.service}#{datetime.utcnow().strftime('%Y-%m-%d')}"
            record_dict['sort_key'] = f"{usage_record.timestamp}#{usage_record.session_id}"
            
            table.put_item(Item=record_dict)
            
        except Exception as e:
            logger.error(f"Failed to store usage record: {e}")
            raise
    
    def _send_usage_metrics(self, usage_record: AIModelUsage):
        """Send usage metrics to CloudWatch"""
        
        try:
            metric_data = [
                {
                    'MetricName': 'TokensProcessed',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': usage_record.service},
                        {'Name': 'Model', 'Value': usage_record.model},
                        {'Name': 'QueryType', 'Value': usage_record.query_type}
                    ],
                    'Value': usage_record.tokens_input + usage_record.tokens_output,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'AIServiceCost',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': usage_record.service},
                        {'Name': 'Model', 'Value': usage_record.model}
                    ],
                    'Value': float(usage_record.total_cost),
                    'Unit': 'None'  # Cost in USD
                },
                {
                    'MetricName': 'ResponseTime',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': usage_record.service},
                        {'Name': 'Model', 'Value': usage_record.model}
                    ],
                    'Value': usage_record.response_time_ms,
                    'Unit': 'Milliseconds'
                },
                {
                    'MetricName': 'APISuccess',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': usage_record.service},
                        {'Name': 'Model', 'Value': usage_record.model}
                    ],
                    'Value': 1 if usage_record.success else 0,
                    'Unit': 'Count'
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='HealthAI/AI-Usage',
                MetricData=metric_data
            )
            
        except Exception as e:
            logger.error(f"Failed to send usage metrics: {e}")
    
    def _check_budget_thresholds(self, current_cost: Decimal):
        """Check if current usage exceeds budget thresholds"""
        
        try:
            # Get current period costs
            daily_cost = self._get_period_cost('daily')
            weekly_cost = self._get_period_cost('weekly')
            monthly_cost = self._get_period_cost('monthly')
            
            alerts = []
            
            # Check daily threshold
            if daily_cost >= self.budget_thresholds['daily']:
                alerts.append({
                    'period': 'daily',
                    'current_cost': daily_cost,
                    'threshold': self.budget_thresholds['daily'],
                    'percentage': (daily_cost / self.budget_thresholds['daily']) * 100
                })
            
            # Check weekly threshold  
            if weekly_cost >= self.budget_thresholds['weekly']:
                alerts.append({
                    'period': 'weekly',
                    'current_cost': weekly_cost,
                    'threshold': self.budget_thresholds['weekly'],
                    'percentage': (weekly_cost / self.budget_thresholds['weekly']) * 100
                })
            
            # Check monthly threshold
            if monthly_cost >= self.budget_thresholds['monthly']:
                alerts.append({
                    'period': 'monthly',
                    'current_cost': monthly_cost,
                    'threshold': self.budget_thresholds['monthly'],
                    'percentage': (monthly_cost / self.budget_thresholds['monthly']) * 100
                })
            
            # Send alerts if thresholds exceeded
            if alerts:
                self._send_budget_alerts(alerts)
                
        except Exception as e:
            logger.error(f"Failed to check budget thresholds: {e}")
    
    def _get_period_cost(self, period: str) -> Decimal:
        """Get total cost for specified period"""
        
        try:
            # Calculate date range
            now = datetime.utcnow()
            
            if period == 'daily':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == 'weekly':
                start_date = now - timedelta(days=7)
            elif period == 'monthly':
                start_date = now - timedelta(days=30)
            else:
                return Decimal('0')
            
            # Query CloudWatch metrics for cost data
            response = self.cloudwatch.get_metric_statistics(
                Namespace='HealthAI/AI-Usage',
                MetricName='AIServiceCost',
                StartTime=start_date,
                EndTime=now,
                Period=3600,  # 1 hour periods
                Statistics=['Sum']
            )
            
            total_cost = sum(Decimal(str(point['Sum'])) for point in response.get('Datapoints', []))
            return total_cost
            
        except Exception as e:
            logger.error(f"Failed to get period cost: {e}")
            return Decimal('0')
    
    def _send_budget_alerts(self, alerts: List[Dict]):
        """Send budget threshold alerts"""
        
        try:
            alert_message = "🚨 HealthAI AI Model Budget Alert\n\n"
            
            for alert in alerts:
                alert_message += f"Period: {alert['period'].title()}\n"
                alert_message += f"Current Cost: ${float(alert['current_cost']):.2f}\n"
                alert_message += f"Budget Threshold: ${float(alert['threshold']):.2f}\n"
                alert_message += f"Usage: {float(alert['percentage']):.1f}%\n\n"
            
            alert_message += "Consider implementing cost optimization measures:\n"
            alert_message += "• Switch to more cost-effective models\n"
            alert_message += "• Implement response caching\n"
            alert_message += "• Add query complexity limits\n"
            alert_message += "• Review and optimize prompts\n"
            
            # Send SNS notification
            self.sns.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789012:healthai-cost-alerts',
                Message=alert_message,
                Subject=f'HealthAI - AI Model Budget Alert ({len(alerts)} thresholds exceeded)'
            )
            
            logger.warning(f"Budget alert sent for {len(alerts)} exceeded thresholds")
            
        except Exception as e:
            logger.error(f"Failed to send budget alerts: {e}")
    
    def generate_cost_report(self, days_back: int = 7) -> Dict:
        """Generate comprehensive cost analysis report"""
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            # Get usage data from DynamoDB
            usage_data = self._query_usage_data(start_time, end_time)
            
            # Calculate totals by service and model
            service_costs = {}
            model_costs = {}
            daily_costs = {}
            query_type_costs = {}
            
            for record in usage_data:
                service = record['service']
                model = record['model']
                cost = Decimal(record['total_cost'])
                query_type = record['query_type']
                date = record['timestamp'][:10]  # YYYY-MM-DD
                
                # Aggregate by service
                service_costs[service] = service_costs.get(service, Decimal('0')) + cost
                
                # Aggregate by model
                model_key = f"{service}/{model}"
                model_costs[model_key] = model_costs.get(model_key, Decimal('0')) + cost
                
                # Aggregate by date
                daily_costs[date] = daily_costs.get(date, Decimal('0')) + cost
                
                # Aggregate by query type
                query_type_costs[query_type] = query_type_costs.get(query_type, Decimal('0')) + cost
            
            total_cost = sum(service_costs.values())
            
            # Generate recommendations
            recommendations = self._generate_cost_recommendations(service_costs, model_costs)
            
            report = {
                'report_period': {
                    'start_date': start_time.isoformat(),
                    'end_date': end_time.isoformat(),
                    'days_covered': days_back
                },
                'cost_summary': {
                    'total_cost': float(total_cost),
                    'daily_average': float(total_cost / days_back),
                    'projected_monthly': float(total_cost / days_back * 30)
                },
                'cost_by_service': {k: float(v) for k, v in service_costs.items()},
                'cost_by_model': {k: float(v) for k, v in model_costs.items()},
                'cost_by_query_type': {k: float(v) for k, v in query_type_costs.items()},
                'daily_breakdown': {k: float(v) for k, v in daily_costs.items()},
                'budget_status': {
                    'daily_budget': float(self.budget_thresholds['daily']),
                    'weekly_budget': float(self.budget_thresholds['weekly']),
                    'monthly_budget': float(self.budget_thresholds['monthly']),
                    'current_daily_usage': float(daily_costs.get(end_time.strftime('%Y-%m-%d'), Decimal('0'))),
                    'budget_utilization_daily': float((daily_costs.get(end_time.strftime('%Y-%m-%d'), Decimal('0')) / self.budget_thresholds['daily']) * 100)
                },
                'recommendations': recommendations,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate cost report: {e}")
            return {'error': 'Failed to generate cost report', 'details': str(e)}
    
    def _query_usage_data(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Query usage data from DynamoDB for date range"""
        
        # This would implement actual DynamoDB query logic
        # For now, return mock data structure
        return [
            {
                'service': 'gemini',
                'model': '1.5-pro',
                'total_cost': '0.0045',
                'query_type': 'medical',
                'timestamp': '2024-10-24T10:00:00Z'
            }
            # ... more records
        ]
    
    def _generate_cost_recommendations(self, service_costs: Dict, model_costs: Dict) -> List[str]:
        """Generate cost optimization recommendations"""
        
        recommendations = []
        
        # Check for expensive models
        for model, cost in model_costs.items():
            if cost > Decimal('10.00'):  # $10+ per week
                if 'gemini-1.5-pro' in model:
                    recommendations.append(f"Consider using Gemini 1.5 Flash for simple queries instead of Pro model (current cost: ${float(cost):.2f})")
                elif 'groq-llama3-70b' in model:
                    recommendations.append(f"Consider using Mixtral 8x7B for less complex queries (current cost: ${float(cost):.2f})")
        
        # Check service distribution
        total_cost = sum(service_costs.values())
        if total_cost > Decimal('50.00'):  # $50+ per week
            recommendations.append("Implement response caching to reduce repeat API calls")
            recommendations.append("Add query complexity analysis to route simple queries to cheaper models")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Current costs are within acceptable limits")
            recommendations.append("Continue monitoring for optimization opportunities")
        
        return recommendations