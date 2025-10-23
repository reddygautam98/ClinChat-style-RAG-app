"""
Real-time Performance Monitoring Dashboard for HealthAI RAG
Comprehensive monitoring and alerting system
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path
import logging
from collections import defaultdict, deque


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    timestamp: datetime
    metric_name: str
    value: float
    metadata: Dict[str, Any]
    

@dataclass
class AlertRule:
    """Performance alert configuration"""
    name: str
    metric_name: str
    threshold: float
    comparison: str  # "greater_than", "less_than", "equals"
    window_minutes: int
    min_samples: int
    enabled: bool = True


class PerformanceMonitor:
    """Real-time performance monitoring system"""
    
    def __init__(self, db_path: str = "data/performance_metrics.db"):
        self.db_path = db_path
        self.metrics_buffer = deque(maxlen=10000)  # In-memory buffer
        self.alert_rules: List[AlertRule] = []
        self.recent_alerts = deque(maxlen=100)
        
        # Initialize database
        self._init_database()
        
        # Set up default alert rules
        self._setup_default_alerts()
        
        # Performance counters
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON performance_metrics(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name 
                ON performance_metrics(metric_name)
            """)
    
    def _setup_default_alerts(self):
        """Set up default performance alerts"""
        default_alerts = [
            AlertRule(
                name="High Response Time",
                metric_name="response_time",
                threshold=5.0,  # 5 seconds
                comparison="greater_than",
                window_minutes=5,
                min_samples=3
            ),
            AlertRule(
                name="Low Confidence Score",
                metric_name="confidence_score", 
                threshold=0.3,
                comparison="less_than",
                window_minutes=10,
                min_samples=5
            ),
            AlertRule(
                name="High Error Rate",
                metric_name="error_rate",
                threshold=0.05,  # 5%
                comparison="greater_than", 
                window_minutes=5,
                min_samples=10
            ),
            AlertRule(
                name="API Quota Near Limit",
                metric_name="api_usage_percentage",
                threshold=85.0,  # 85%
                comparison="greater_than",
                window_minutes=60,
                min_samples=1
            )
        ]
        
        self.alert_rules.extend(default_alerts)
    
    def record_metric(self, metric_name: str, value: float, 
                     metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        if metadata is None:
            metadata = {}
            
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=metric_name,
            value=value,
            metadata=metadata
        )
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        
        # Update counters
        self.counters[metric_name] += 1
        self.timers[metric_name].append(value)
        
        # Keep only recent values for timers (last 1000)
        if len(self.timers[metric_name]) > 1000:
            self.timers[metric_name] = self.timers[metric_name][-1000:]
        
        # Check alerts
        self._check_alerts(metric)
        
        # Periodically flush to database
        if len(self.metrics_buffer) >= 100:
            self._flush_metrics_to_db()
    
    def _flush_metrics_to_db(self):
        """Flush metrics buffer to database"""
        if not self.metrics_buffer:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for metric in self.metrics_buffer:
                cursor.execute("""
                    INSERT INTO performance_metrics 
                    (timestamp, metric_name, value, metadata)
                    VALUES (?, ?, ?, ?)
                """, (
                    metric.timestamp.isoformat(),
                    metric.metric_name,
                    metric.value,
                    json.dumps(metric.metadata)
                ))
            
            conn.commit()
        
        self.metrics_buffer.clear()
        self.logger.info(f"Flushed {len(self.metrics_buffer)} metrics to database")
    
    def _check_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any alerts"""
        for rule in self.alert_rules:
            if not rule.enabled or rule.metric_name != metric.metric_name:
                continue
                
            # Get recent values for this metric
            cutoff_time = datetime.now() - timedelta(minutes=rule.window_minutes)
            recent_values = [
                m.value for m in self.metrics_buffer
                if (m.metric_name == rule.metric_name and 
                    m.timestamp >= cutoff_time)
            ]
            
            if len(recent_values) < rule.min_samples:
                continue
                
            # Check threshold
            triggered = False
            if rule.comparison == "greater_than":
                triggered = any(v > rule.threshold for v in recent_values)
            elif rule.comparison == "less_than":
                triggered = any(v < rule.threshold for v in recent_values)
            elif rule.comparison == "equals":
                triggered = any(abs(v - rule.threshold) < 0.01 for v in recent_values)
            
            if triggered:
                self._trigger_alert(rule, metric, recent_values)
    
    def _trigger_alert(self, rule: AlertRule, metric: PerformanceMetric, 
                      recent_values: List[float]):
        """Trigger a performance alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "rule_name": rule.name,
            "metric_name": rule.metric_name,
            "current_value": metric.value,
            "threshold": rule.threshold,
            "recent_values": recent_values[-5:],  # Last 5 values
            "severity": self._calculate_alert_severity(rule, metric.value),
            "metadata": metric.metadata
        }
        
        self.recent_alerts.append(alert)
        self.logger.warning(f"ALERT: {rule.name} - {metric.metric_name}={metric.value}")
        
        # Could integrate with external alerting systems here
        self._send_alert_notification(alert)
    
    def _calculate_alert_severity(self, rule: AlertRule, value: float) -> str:
        """Calculate alert severity based on how far value is from threshold"""
        threshold_diff = abs(value - rule.threshold) / rule.threshold
        
        if threshold_diff > 0.5:
            return "critical"
        elif threshold_diff > 0.2:
            return "high"
        elif threshold_diff > 0.1:
            return "medium"
        else:
            return "low"
    
    def _send_alert_notification(self, alert: Dict[str, Any]):
        """Send alert notification (webhook, email, etc.)"""
        # Placeholder for external notification system
        pass
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics summary"""
        now = datetime.now()
        
        # Calculate averages for last hour
        hour_ago = now - timedelta(hours=1)
        recent_metrics = [
            m for m in self.metrics_buffer
            if m.timestamp >= hour_ago
        ]
        
        metrics_summary = {}
        
        # Group by metric name
        by_metric = defaultdict(list)
        for metric in recent_metrics:
            by_metric[metric.metric_name].append(metric.value)
        
        for metric_name, values in by_metric.items():
            if values:
                metrics_summary[metric_name] = {
                    "current": values[-1],
                    "average_1h": sum(values) / len(values),
                    "min_1h": min(values),
                    "max_1h": max(values),
                    "count_1h": len(values)
                }
        
        return {
            "timestamp": now.isoformat(),
            "metrics": metrics_summary,
            "active_alerts": len([a for a in self.recent_alerts 
                                if datetime.fromisoformat(a["timestamp"]) >= hour_ago]),
            "total_queries_1h": sum(self.counters.values()),
            "system_health": self._calculate_system_health()
        }
    
    def _calculate_system_health(self) -> str:
        """Calculate overall system health score"""
        recent_alerts = [
            a for a in self.recent_alerts
            if datetime.fromisoformat(a["timestamp"]) >= datetime.now() - timedelta(hours=1)
        ]
        
        critical_alerts = [a for a in recent_alerts if a["severity"] == "critical"]
        high_alerts = [a for a in recent_alerts if a["severity"] == "high"]
        
        if critical_alerts:
            return "critical"
        elif len(high_alerts) > 3:
            return "degraded"
        elif len(recent_alerts) > 5:
            return "warning"
        else:
            return "healthy"
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Generate performance dashboard data"""
        current_metrics = self.get_current_metrics()
        
        dashboard = {
            "overview": {
                "system_health": current_metrics["system_health"],
                "total_queries_1h": current_metrics["total_queries_1h"],
                "active_alerts": current_metrics["active_alerts"],
                "last_updated": current_metrics["timestamp"]
            },
            "key_metrics": current_metrics["metrics"],
            "recent_alerts": list(self.recent_alerts)[-10:],  # Last 10 alerts
            "performance_trends": self._calculate_performance_trends(),
            "model_usage": self._get_model_usage_stats(),
            "api_usage": self._get_api_usage_stats()
        }
        
        return dashboard
    
    def _calculate_performance_trends(self) -> Dict[str, str]:
        """Calculate performance trends (improving/degrading)"""
        trends = {}
        
        for metric_name in ["response_time", "confidence_score", "error_rate"]:
            if metric_name not in self.timers or len(self.timers[metric_name]) < 20:
                trends[metric_name] = "insufficient_data"
                continue
            
            values = self.timers[metric_name]
            recent_avg = sum(values[-10:]) / 10 if len(values) >= 10 else sum(values) / len(values)
            older_avg = sum(values[-20:-10]) / 10 if len(values) >= 20 else recent_avg
            
            if recent_avg < older_avg * 0.95:  # 5% improvement threshold
                trends[metric_name] = "improving"
            elif recent_avg > older_avg * 1.05:  # 5% degradation threshold
                trends[metric_name] = "degrading"
            else:
                trends[metric_name] = "stable"
        
        return trends
    
    def _get_model_usage_stats(self) -> Dict[str, Any]:
        """Get AI model usage statistics"""
        # Extract from recent metrics metadata
        model_usage = defaultdict(int)
        
        for metric in list(self.metrics_buffer)[-1000:]:  # Last 1000 metrics
            if "model_used" in metric.metadata:
                model_usage[metric.metadata["model_used"]] += 1
        
        total_requests = sum(model_usage.values())
        
        return {
            "total_requests": total_requests,
            "model_distribution": {
                model: count / total_requests * 100 if total_requests > 0 else 0
                for model, count in model_usage.items()
            }
        }
    
    def _get_api_usage_stats(self) -> Dict[str, Any]:
        """Get API usage and cost statistics"""
        # Placeholder for API usage tracking
        return {
            "gemini_requests_today": self.counters.get("gemini_api_calls", 0),
            "groq_requests_today": self.counters.get("groq_api_calls", 0),
            "estimated_cost_today": 0.0,  # Calculate based on API pricing
            "quota_usage_percentage": 45.0  # Example
        }


class RAGPerformanceTracker:
    """Track RAG-specific performance metrics"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    def track_query(self, query: str, response: Dict[str, Any], 
                   processing_time: float):
        """Track metrics for a RAG query"""
        
        # Basic metrics
        self.monitor.record_metric("response_time", processing_time, {
            "query_length": len(query),
            "model_used": response.get("model_used", "unknown")
        })
        
        self.monitor.record_metric("confidence_score", 
                                 response.get("confidence", 0.0), {
            "fusion_strategy": response.get("fusion_strategy", "none")
        })
        
        # Document retrieval metrics
        sources = response.get("sources", [])
        self.monitor.record_metric("documents_retrieved", len(sources))
        
        # Response quality metrics
        response_length = len(response.get("answer", ""))
        self.monitor.record_metric("response_length", response_length)
        
        # Model-specific tracking
        model_used = response.get("model_used", "unknown")
        self.monitor.record_metric(f"{model_used}_usage", 1.0)
    
    def track_error(self, error_type: str, query: str, error_details: str):
        """Track error metrics"""
        self.monitor.record_metric("error_count", 1.0, {
            "error_type": error_type,
            "query_length": len(query),
            "error_details": error_details
        })
        
        # Calculate error rate
        total_queries = self.monitor.counters["total_queries"]
        error_count = self.monitor.counters["error_count"] 
        error_rate = error_count / max(total_queries, 1)
        
        self.monitor.record_metric("error_rate", error_rate)


# Usage example
def demo_performance_monitoring():
    """Demonstrate performance monitoring system"""
    
    # Initialize monitor
    monitor = PerformanceMonitor()
    tracker = RAGPerformanceTracker(monitor)
    
    # Simulate some queries
    import random
    
    queries = [
        "What are the symptoms of diabetes?",
        "How is hypertension treated?", 
        "What causes heart disease?",
        "Explain COVID-19 symptoms",
        "Treatment options for asthma"
    ]
    
    print("🚀 Simulating RAG queries...")
    
    for i in range(50):
        query = random.choice(queries)
        processing_time = random.uniform(0.5, 3.0)
        
        # Simulate response
        response = {
            "answer": f"Medical response for query {i}",
            "confidence": random.uniform(0.6, 0.95),
            "model_used": random.choice(["gemini", "groq", "fusion"]),
            "fusion_strategy": "weighted_average",
            "sources": [f"doc_{j}" for j in range(random.randint(2, 6))]
        }
        
        # Track metrics
        tracker.track_query(query, response, processing_time)
        
        # Simulate occasional errors
        if random.random() < 0.05:  # 5% error rate
            tracker.track_error("api_timeout", query, "Request timed out")
    
    # Generate dashboard
    dashboard = monitor.get_performance_dashboard()
    
    print("\n📊 Performance Dashboard:")
    print(f"System Health: {dashboard['overview']['system_health']}")
    print(f"Queries (1h): {dashboard['overview']['total_queries_1h']}")
    print(f"Active Alerts: {dashboard['overview']['active_alerts']}")
    
    print("\n📈 Key Metrics:")
    for metric_name, stats in dashboard['key_metrics'].items():
        print(f"  {metric_name}: {stats['average_1h']:.3f} (avg 1h)")
    
    print(f"\n🔔 Recent Alerts: {len(dashboard['recent_alerts'])}")
    for alert in dashboard['recent_alerts'][-3:]:
        print(f"  - {alert['rule_name']}: {alert['metric_name']}={alert['current_value']}")


if __name__ == "__main__":
    demo_performance_monitoring()