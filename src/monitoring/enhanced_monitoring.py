"""
Enhanced monitoring system for HealthAI RAG Application
Provides comprehensive metrics collection, alerting, and observability
"""

import time
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict, deque
import logging
import json
import threading
import statistics

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: float
    value: float
    labels: Dict[str, str]
    metric_name: str


@dataclass
class Alert:
    """Alert definition and state"""
    name: str
    condition: str
    threshold: float
    comparison: str  # "gt", "lt", "eq", "gte", "lte"
    duration: int  # seconds
    severity: str  # "critical", "warning", "info"
    description: str
    enabled: bool = True
    triggered_at: Optional[float] = None
    resolved_at: Optional[float] = None
    notification_sent: bool = False


class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self, retention_hours: int = 24):
        """
        Initialize metrics collector
        
        Args:
            retention_hours: How long to keep metrics in memory
        """
        self.retention_hours = retention_hours
        self.metrics = defaultdict(lambda: deque())
        self.retention_seconds = retention_hours * 3600
        self.collection_interval = 30  # seconds
        self.collecting = False
        self.collection_thread = None
        
        # Custom metrics
        self.custom_counters = defaultdict(float)
        self.custom_gauges = defaultdict(float)
        self.custom_histograms = defaultdict(list)
        
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric data point"""
        labels = labels or {}
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels,
            metric_name=name
        )
        
        self.metrics[name].append(point)
        self._cleanup_old_metrics(name)
    
    def _cleanup_old_metrics(self, metric_name: str):
        """Remove old metric points outside retention window"""
        cutoff_time = time.time() - self.retention_seconds
        
        while (self.metrics[metric_name] and 
               self.metrics[metric_name][0].timestamp < cutoff_time):
            self.metrics[metric_name].popleft()
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        self.custom_counters[key] += 1
        self.record_metric(f"counter_{name}", self.custom_counters[key], labels)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value"""
        key = self._make_key(name, labels)
        self.custom_gauges[key] = value
        self.record_metric(f"gauge_{name}", value, labels)
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Add observation to histogram metric"""
        key = self._make_key(name, labels)
        self.custom_histograms[key].append(value)
        
        # Keep only last 1000 observations per histogram
        if len(self.custom_histograms[key]) > 1000:
            self.custom_histograms[key] = self.custom_histograms[key][-1000:]
        
        # Record percentiles
        values = self.custom_histograms[key]
        if values:
            for percentile in [50, 95, 99]:
                p_value = statistics.quantiles(values, n=100)[percentile-1] if len(values) > 1 else values[0]
                self.record_metric(f"histogram_{name}_p{percentile}", p_value, labels)
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key from metric name and labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"
    
    def get_metric_values(self, name: str, since: Optional[float] = None) -> List[MetricPoint]:
        """Get metric values, optionally filtered by time"""
        points = list(self.metrics[name])
        if since:
            points = [p for p in points if p.timestamp >= since]
        return points
    
    def get_latest_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get the most recent value for a metric"""
        points = self.get_metric_values(name)
        if not points:
            return None
        
        if labels:
            # Filter by labels
            matching_points = [p for p in points if all(
                p.labels.get(k) == v for k, v in labels.items()
            )]
            if matching_points:
                return matching_points[-1].value
        else:
            return points[-1].value
        
        return None


class SystemMetricsCollector:
    """Collects system-level metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        
    def collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.record_metric("system_cpu_percent", cpu_percent)
            
            cpu_count = psutil.cpu_count()
            self.metrics.record_metric("system_cpu_count", cpu_count)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics.record_metric("system_memory_total_bytes", memory.total)
            self.metrics.record_metric("system_memory_used_bytes", memory.used)
            self.metrics.record_metric("system_memory_percent", memory.percent)
            self.metrics.record_metric("system_memory_available_bytes", memory.available)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.metrics.record_metric("system_disk_total_bytes", disk.total)
            self.metrics.record_metric("system_disk_used_bytes", disk.used)
            self.metrics.record_metric("system_disk_percent", (disk.used / disk.total) * 100)
            
            # Network metrics
            network = psutil.net_io_counters()
            self.metrics.record_metric("system_network_bytes_sent", network.bytes_sent)
            self.metrics.record_metric("system_network_bytes_recv", network.bytes_recv)
            self.metrics.record_metric("system_network_packets_sent", network.packets_sent)
            self.metrics.record_metric("system_network_packets_recv", network.packets_recv)
            
            # Process metrics
            process = psutil.Process()
            self.metrics.record_metric("process_cpu_percent", process.cpu_percent())
            self.metrics.record_metric("process_memory_rss_bytes", process.memory_info().rss)
            self.metrics.record_metric("process_memory_vms_bytes", process.memory_info().vms)
            self.metrics.record_metric("process_open_files", len(process.open_files()))
            self.metrics.record_metric("process_connections", len(process.connections()))
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")


class ApplicationMetricsCollector:
    """Collects application-specific metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.request_durations = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        
    def record_request(self, duration: float, status_code: int, endpoint: str):
        """Record API request metrics"""
        self.request_durations.append(duration)
        
        labels = {"endpoint": endpoint, "status_code": str(status_code)}
        self.metrics.record_metric("http_request_duration_seconds", duration, labels)
        self.metrics.increment_counter("http_requests_total", labels)
        
        if status_code >= 400:
            self.error_counts[endpoint] += 1
            self.metrics.increment_counter("http_errors_total", labels)
    
    def record_rag_query(self, duration: float, num_results: int, success: bool):
        """Record RAG query metrics"""
        labels = {"success": str(success)}
        
        self.metrics.record_metric("rag_query_duration_seconds", duration, labels)
        self.metrics.record_metric("rag_results_count", num_results, labels)
        self.metrics.increment_counter("rag_queries_total", labels)
    
    def record_vector_search(self, duration: float, similarity_scores: List[float]):
        """Record vector search metrics"""
        self.metrics.record_metric("vector_search_duration_seconds", duration)
        
        if similarity_scores:
            avg_score = statistics.mean(similarity_scores)
            max_score = max(similarity_scores)
            self.metrics.record_metric("vector_search_avg_similarity", avg_score)
            self.metrics.record_metric("vector_search_max_similarity", max_score)
    
    def record_ai_service_call(self, service: str, duration: float, success: bool, tokens_used: int = 0):
        """Record AI service call metrics"""
        labels = {"service": service, "success": str(success)}
        
        self.metrics.record_metric("ai_service_duration_seconds", duration, labels)
        self.metrics.increment_counter("ai_service_calls_total", labels)
        
        if tokens_used > 0:
            self.metrics.record_metric("ai_service_tokens_used", tokens_used, labels)


class AlertManager:
    """Manages alerting rules and notifications"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts = {}
        self.notification_handlers = []
        self.evaluation_interval = 30  # seconds
        self.evaluating = False
        self.evaluation_thread = None
        
    def add_alert(self, alert: Alert):
        """Add an alert rule"""
        self.alerts[alert.name] = alert
        logger.info(f"Added alert rule: {alert.name}")
    
    def remove_alert(self, name: str):
        """Remove an alert rule"""
        if name in self.alerts:
            del self.alerts[name]
            logger.info(f"Removed alert rule: {name}")
    
    def add_notification_handler(self, handler: Callable[[Alert, str], None]):
        """Add notification handler function"""
        self.notification_handlers.append(handler)
    
    def evaluate_alerts(self):
        """Evaluate all alert conditions"""
        current_time = time.time()
        
        for alert in self.alerts.values():
            if not alert.enabled:
                continue
                
            try:
                # Get current metric value
                current_value = self.metrics.get_latest_value(alert.condition)
                
                if current_value is None:
                    continue
                
                # Check if condition is met
                condition_met = self._evaluate_condition(
                    current_value, alert.threshold, alert.comparison
                )
                
                if condition_met and not alert.triggered_at:
                    # Check if condition has been met for required duration
                    duration_check = self._check_duration(alert, current_time)
                    
                    if duration_check:
                        self._trigger_alert(alert, current_time, current_value)
                
                elif not condition_met and alert.triggered_at:
                    self._resolve_alert(alert, current_time)
                    
            except Exception as e:
                logger.error(f"Failed to evaluate alert {alert.name}: {e}")
    
    def _evaluate_condition(self, value: float, threshold: float, comparison: str) -> bool:
        """Evaluate alert condition"""
        if comparison == "gt":
            return value > threshold
        elif comparison == "lt":
            return value < threshold
        elif comparison == "eq":
            return value == threshold
        elif comparison == "gte":
            return value >= threshold
        elif comparison == "lte":
            return value <= threshold
        else:
            return False
    
    def _check_duration(self, alert: Alert, current_time: float) -> bool:
        """Check if condition has been met for required duration"""
        if alert.duration <= 0:
            return True
        
        # Get historical values for duration check
        since_time = current_time - alert.duration
        historical_points = self.metrics.get_metric_values(alert.condition, since_time)
        
        if len(historical_points) < 2:
            return False
        
        # Check if all values in duration window meet condition
        all_meet_condition = all(
            self._evaluate_condition(point.value, alert.threshold, alert.comparison)
            for point in historical_points
        )
        
        return all_meet_condition
    
    def _trigger_alert(self, alert: Alert, trigger_time: float, current_value: float):
        """Trigger an alert"""
        alert.triggered_at = trigger_time
        alert.resolved_at = None
        alert.notification_sent = False
        
        message = f"ALERT: {alert.name} - {alert.description} (Value: {current_value}, Threshold: {alert.threshold})"
        
        logger.warning(message)
        
        # Send notifications
        for handler in self.notification_handlers:
            try:
                handler(alert, message)
                alert.notification_sent = True
            except Exception as e:
                logger.error(f"Failed to send alert notification: {e}")
    
    def _resolve_alert(self, alert: Alert, resolve_time: float):
        """Resolve an alert"""
        alert.resolved_at = resolve_time
        duration = resolve_time - alert.triggered_at if alert.triggered_at else 0
        
        message = f"RESOLVED: {alert.name} - Duration: {duration:.1f}s"
        
        logger.info(message)
        
        # Send resolution notifications
        for handler in self.notification_handlers:
            try:
                handler(alert, message)
            except Exception as e:
                logger.error(f"Failed to send resolution notification: {e}")
        
        # Reset alert state
        alert.triggered_at = None
    
    def start_evaluation(self):
        """Start alert evaluation loop"""
        if self.evaluating:
            logger.warning("Alert evaluation already running")
            return
        
        self.evaluating = True
        self.evaluation_thread = threading.Thread(target=self._evaluation_loop, daemon=True)
        self.evaluation_thread.start()
        
        logger.info("Alert evaluation started")
    
    def stop_evaluation(self):
        """Stop alert evaluation loop"""
        self.evaluating = False
        
        if self.evaluation_thread and self.evaluation_thread.is_alive():
            self.evaluation_thread.join(timeout=5)
        
        logger.info("Alert evaluation stopped")
    
    def _evaluation_loop(self):
        """Alert evaluation background loop"""
        while self.evaluating:
            try:
                self.evaluate_alerts()
                time.sleep(self.evaluation_interval)
            except Exception as e:
                logger.error(f"Alert evaluation loop error: {e}")
                time.sleep(5)  # Brief pause on error
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of currently active alerts"""
        active = []
        
        for alert in self.alerts.values():
            if alert.triggered_at and not alert.resolved_at:
                active.append({
                    "name": alert.name,
                    "severity": alert.severity,
                    "description": alert.description,
                    "triggered_at": alert.triggered_at,
                    "duration": time.time() - alert.triggered_at
                })
        
        return active


class MonitoringDashboard:
    """Generates monitoring dashboard data"""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics = metrics_collector
        self.alerts = alert_manager
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data"""
        current_time = time.time()
        
        return {
            "timestamp": current_time,
            "system_health": self._get_system_health(),
            "application_metrics": self._get_application_metrics(),
            "performance_summary": self._get_performance_summary(),
            "active_alerts": self.alerts.get_active_alerts(),
            "recent_trends": self._get_recent_trends()
        }
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health overview"""
        return {
            "cpu_usage": self.metrics.get_latest_value("system_cpu_percent"),
            "memory_usage": self.metrics.get_latest_value("system_memory_percent"),
            "disk_usage": self.metrics.get_latest_value("system_disk_percent"),
            "process_memory_mb": (self.metrics.get_latest_value("process_memory_rss_bytes") or 0) / (1024 * 1024)
        }
    
    def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        return {
            "total_requests": self.metrics.get_latest_value("counter_http_requests_total"),
            "total_errors": self.metrics.get_latest_value("counter_http_errors_total"),
            "rag_queries": self.metrics.get_latest_value("counter_rag_queries_total"),
            "ai_service_calls": self.metrics.get_latest_value("counter_ai_service_calls_total")
        }
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        return {
            "avg_request_time": self.metrics.get_latest_value("histogram_http_request_duration_seconds_p50"),
            "p95_request_time": self.metrics.get_latest_value("histogram_http_request_duration_seconds_p95"),
            "avg_rag_query_time": self.metrics.get_latest_value("histogram_rag_query_duration_seconds_p50"),
            "vector_search_performance": self.metrics.get_latest_value("vector_search_avg_similarity")
        }
    
    def _get_recent_trends(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get recent metric trends for charting"""
        since_time = time.time() - 3600  # Last hour
        
        trends = {}
        
        key_metrics = [
            "system_cpu_percent",
            "system_memory_percent",
            "http_request_duration_seconds",
            "rag_query_duration_seconds"
        ]
        
        for metric in key_metrics:
            points = self.metrics.get_metric_values(metric, since_time)
            trends[metric] = [
                {"timestamp": p.timestamp, "value": p.value}
                for p in points[-60:]  # Last 60 points
            ]
        
        return trends


class EnhancedMonitoringSystem:
    """Main monitoring system coordinator"""
    
    def __init__(self, retention_hours: int = 24):
        self.metrics_collector = MetricsCollector(retention_hours)
        self.system_collector = SystemMetricsCollector(self.metrics_collector)
        self.app_collector = ApplicationMetricsCollector(self.metrics_collector)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.dashboard = MonitoringDashboard(self.metrics_collector, self.alert_manager)
        
        self.collection_thread = None
        self.collecting = False
        
        # Setup default alerts
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        default_alerts = [
            Alert(
                name="high_cpu_usage",
                condition="system_cpu_percent",
                threshold=80.0,
                comparison="gte",
                duration=300,  # 5 minutes
                severity="warning",
                description="CPU usage is consistently high"
            ),
            Alert(
                name="high_memory_usage", 
                condition="system_memory_percent",
                threshold=90.0,
                comparison="gte",
                duration=180,  # 3 minutes
                severity="critical",
                description="Memory usage is critically high"
            ),
            Alert(
                name="slow_api_response",
                condition="histogram_http_request_duration_seconds_p95",
                threshold=5.0,
                comparison="gt",
                duration=120,  # 2 minutes
                severity="warning",
                description="API response times are slow"
            ),
            Alert(
                name="high_error_rate",
                condition="counter_http_errors_total",
                threshold=10.0,
                comparison="gt",
                duration=60,  # 1 minute
                severity="critical",
                description="High error rate detected"
            )
        ]
        
        for alert in default_alerts:
            self.alert_manager.add_alert(alert)
    
    def start_monitoring(self):
        """Start the monitoring system"""
        if self.collecting:
            logger.warning("Monitoring already started")
            return
        
        self.collecting = True
        
        # Start metrics collection
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        # Start alert evaluation
        self.alert_manager.start_evaluation()
        
        logger.info("Enhanced monitoring system started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.collecting = False
        
        # Stop collection thread
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=5)
        
        # Stop alert evaluation
        self.alert_manager.stop_evaluation()
        
        logger.info("Enhanced monitoring system stopped")
    
    def _collection_loop(self):
        """Background metrics collection loop"""
        while self.collecting:
            try:
                self.system_collector.collect_system_metrics()
                time.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(5)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard.generate_dashboard_data()
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        if format == "json":
            dashboard_data = self.get_dashboard_data()
            return json.dumps(dashboard_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global monitoring instance
monitoring_system = EnhancedMonitoringSystem()


# Notification handlers
def log_notification_handler(alert: Alert, message: str):
    """Log alert notifications"""
    if alert.severity == "critical":
        logger.critical(f"ALERT: {message}")
    elif alert.severity == "warning":
        logger.warning(f"ALERT: {message}")
    else:
        logger.info(f"ALERT: {message}")


def email_notification_handler(alert: Alert, message: str):
    """Email alert notifications (placeholder)"""
    # In production, implement actual email sending
    logger.info(f"EMAIL ALERT: {message}")


def webhook_notification_handler(alert: Alert, message: str):
    """Webhook alert notifications (placeholder)"""
    # In production, implement webhook POST
    logger.info(f"WEBHOOK ALERT: {message}")


# Setup notification handlers
monitoring_system.alert_manager.add_notification_handler(log_notification_handler)