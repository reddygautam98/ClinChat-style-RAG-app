"""
AI Cost Monitoring Dashboard and Automated Budget Controls
"""
import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal

def create_ai_cost_dashboard():
    """Create comprehensive AI cost monitoring dashboard"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    dashboard_config = {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["HealthAI/AI-Usage", "AIServiceCost", "Service", "gemini", {"stat": "Sum"}],
                        [".", ".", ".", "groq", {"stat": "Sum"}]
                    ],
                    "period": 3600,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "AI Service Costs (Hourly)",
                    "yAxis": {"left": {"min": 0}},
                    "annotations": {
                        "horizontal": [
                            {"label": "Daily Budget ($100)", "value": 100},
                            {"label": "Critical Threshold ($80)", "value": 80}
                        ]
                    }
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["HealthAI/AI-Usage", "TokensProcessed", "Service", "gemini", "Model", "1.5-pro"],
                        [".", ".", ".", ".", ".", "1.5-flash"],
                        [".", ".", ".", "groq", ".", "mixtral-8x7b"],
                        [".", ".", ".", ".", ".", "llama3-70b"]
                    ],
                    "period": 3600,
                    "stat": "Sum", 
                    "region": "us-east-1",
                    "title": "Token Usage by Model"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["HealthAI/AI-Usage", "ResponseTime", "Service", "gemini", {"stat": "Average"}],
                        [".", ".", ".", "groq", {"stat": "Average"}]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": "API Response Times",
                    "yAxis": {"left": {"label": "Milliseconds"}}
                }
            },
            {
                "type": "number",
                "properties": {
                    "metrics": [
                        ["HealthAI/AI-Usage", "AIServiceCost", {"stat": "Sum", "period": 86400}]
                    ],
                    "period": 86400,
                    "stat": "Sum",
                    "region": "us-east-1", 
                    "title": "Total Daily Cost",
                    "setPeriodToTimeRange": True
                }
            },
            {
                "type": "log",
                "properties": {
                    "query": "SOURCE '/aws/lambda/healthai-cost-tracker'\n| fields @timestamp, service, model, total_cost, query_type\n| filter @message like /AI Usage tracked/\n| stats sum(total_cost) as daily_cost by service\n| sort daily_cost desc",
                    "region": "us-east-1",
                    "title": "Cost Breakdown by Service (Last 24h)"
                }
            }
        ]
    }
    
    try:
        response = cloudwatch.put_dashboard(
            DashboardName='HealthAI-AI-Cost-Monitoring',
            DashboardBody=json.dumps(dashboard_config)
        )
        print("✅ AI Cost monitoring dashboard created successfully")
        return response
    except Exception as e:
        print(f"❌ Failed to create dashboard: {e}")
        return None

def setup_cost_alarms():
    """Setup CloudWatch alarms for cost thresholds"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    # Daily cost alarm
    cloudwatch.put_metric_alarm(
        AlarmName='HealthAI-Daily-AI-Cost-High',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='AIServiceCost',
        Namespace='HealthAI/AI-Usage',
        Period=86400,  # Daily
        Statistic='Sum',
        Threshold=80.0,  # $80 daily threshold
        ActionsEnabled=True,
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:healthai-cost-alerts'
        ],
        AlarmDescription='Alert when daily AI costs exceed $80',
        Unit='None'
    )
    
    # Hourly spike alarm
    cloudwatch.put_metric_alarm(
        AlarmName='HealthAI-Hourly-AI-Cost-Spike',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='AIServiceCost',
        Namespace='HealthAI/AI-Usage',
        Period=3600,  # Hourly
        Statistic='Sum',
        Threshold=10.0,  # $10 per hour threshold
        ActionsEnabled=True,
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:healthai-cost-alerts'
        ],
        AlarmDescription='Alert when hourly AI costs exceed $10'
    )
    
    # Token usage alarm (cost proxy)
    cloudwatch.put_metric_alarm(
        AlarmName='HealthAI-High-Token-Usage',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='TokensProcessed',
        Namespace='HealthAI/AI-Usage', 
        Period=3600,
        Statistic='Sum',
        Threshold=1000000.0,  # 1M tokens per hour
        ActionsEnabled=True,
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789012:healthai-cost-alerts'
        ],
        AlarmDescription='Alert on high token usage (cost indicator)'
    )

def create_cost_optimization_lambda():
    """Create Lambda function for automated cost optimization"""
    
    lambda_code = """
import json
import boto3
from decimal import Decimal

def lambda_handler(event, context):
    '''Automated cost optimization based on usage patterns'''
    
    cloudwatch = boto3.client('cloudwatch')
    
    try:
        # Get current hour cost
        current_cost = get_current_hour_cost(cloudwatch)
        
        # Optimization actions based on cost
        actions_taken = []
        
        if current_cost > Decimal('15.0'):  # $15/hour is very high
            # Switch to cheaper models
            actions_taken.append("activated_cost_saver_mode")
            update_model_recommendations("cost_priority")
            
        elif current_cost > Decimal('8.0'):  # $8/hour is high
            # Enable response caching 
            actions_taken.append("enabled_aggressive_caching")
            update_caching_policy("aggressive")
            
        elif current_cost > Decimal('5.0'):  # $5/hour is medium-high
            # Switch to balanced mode
            actions_taken.append("switched_to_balanced_mode") 
            update_model_recommendations("balanced")
        
        # Log optimization actions
        if actions_taken:
            send_optimization_notification(current_cost, actions_taken)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'current_cost': float(current_cost),
                'actions_taken': actions_taken,
                'timestamp': context.aws_request_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_current_hour_cost(cloudwatch):
    # Implementation to get current hour cost
    return Decimal('3.50')  # Mock value

def update_model_recommendations(priority):
    # Implementation to update model selection logic
    pass

def update_caching_policy(level):
    # Implementation to update caching behavior  
    pass

def send_optimization_notification(cost, actions):
    # Implementation to send notifications
    pass
"""
    
    # This would create the actual Lambda function
    print("Cost optimization Lambda function code generated")
    print("Deploy this to AWS Lambda with appropriate IAM permissions")

def setup_automated_cost_reports():
    """Setup EventBridge rules for automated cost reporting"""
    
    events = boto3.client('events')
    
    # Daily cost report rule
    rule_response = events.put_rule(
        Name='healthai-daily-cost-report',
        ScheduleExpression='cron(0 9 * * ? *)',  # 9 AM daily
        Description='Generate daily AI cost report',
        State='ENABLED'
    )
    
    # Add Lambda target for cost report generation
    events.put_targets(
        Rule='healthai-daily-cost-report',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:healthai-cost-reporter',
            'Input': json.dumps({
                'report_type': 'daily',
                'recipients': ['finance@healthai.com', 'ops@healthai.com']
            })
        }]
    )
    
    # Weekly detailed cost analysis
    events.put_rule(
        Name='healthai-weekly-cost-analysis',
        ScheduleExpression='cron(0 10 ? * MON *)',  # 10 AM every Monday
        Description='Generate weekly detailed cost analysis',
        State='ENABLED'
    )
    
    events.put_targets(
        Rule='healthai-weekly-cost-analysis',
        Targets=[{
            'Id': '1',
            'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:healthai-cost-analyzer',
            'Input': json.dumps({
                'report_type': 'weekly',
                'include_recommendations': True,
                'recipients': ['cto@healthai.com', 'finance@healthai.com']
            })
        }]
    )
    
    print("✅ Automated cost reporting rules created")

def create_cost_budget():
    """Create AWS Budget for AI service costs"""
    
    budgets = boto3.client('budgets')
    
    budget_config = {
        'BudgetName': 'HealthAI-AI-Services-Monthly',
        'BudgetLimit': {
            'Amount': '2000.00',  # $2000 monthly budget
            'Unit': 'USD'
        },
        'TimeUnit': 'MONTHLY',
        'TimePeriod': {
            'Start': datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        },
        'BudgetType': 'COST',
        'CostFilters': {
            'Service': ['Amazon API Gateway', 'AWS Lambda']  # Proxies for AI service costs
        }
    }
    
    # Budget notifications
    subscribers = [
        {
            'SubscriptionType': 'EMAIL',
            'Address': 'finance@healthai.com'
        },
        {
            'SubscriptionType': 'EMAIL', 
            'Address': 'alerts@healthai.com'
        }
    ]
    
    notifications = [
        {
            'Notification': {
                'NotificationType': 'ACTUAL',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': 80.0  # 80% of budget
            },
            'Subscribers': subscribers
        },
        {
            'Notification': {
                'NotificationType': 'FORECASTED',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': 100.0  # 100% forecasted
            },
            'Subscribers': subscribers
        }
    ]
    
    try:
        budgets.create_budget(
            AccountId='123456789012',  # Replace with actual account ID
            Budget=budget_config,
            NotificationsWithSubscribers=notifications
        )
        print("✅ AI Services budget created with notifications")
    except Exception as e:
        print(f"❌ Failed to create budget: {e}")

if __name__ == "__main__":
    print("🚀 Setting up AI Cost Monitoring Infrastructure...")
    
    # Create dashboard
    create_ai_cost_dashboard()
    
    # Setup alarms  
    setup_cost_alarms()
    
    # Setup automated reporting
    setup_automated_cost_reports()
    
    # Create budget
    create_cost_budget()
    
    # Generate Lambda code
    create_cost_optimization_lambda()
    
    print("✅ AI Cost monitoring infrastructure setup complete!")
    print("\nNext steps:")
    print("1. Deploy the cost optimization Lambda function")
    print("2. Configure SNS topics for cost alerts") 
    print("3. Set up DynamoDB tables for usage tracking")
    print("4. Update application code to use CostAwareAIService")
    print("5. Test cost tracking with sample queries")