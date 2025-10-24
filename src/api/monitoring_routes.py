"""
Monitoring API endpoints for HealthAI RAG Application
Provides REST endpoints for metrics, alerts, and dashboard data
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import time

from ..monitoring.enhanced_monitoring import monitoring_system, Alert

logger = logging.getLogger(__name__)

# Create monitoring router
monitoring_router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MetricQuery(BaseModel):
    """Query model for metric data"""
    metric_name: str
    since: Optional[float] = None
    limit: Optional[int] = 100


class AlertRequest(BaseModel):
    """Request model for creating alerts"""
    name: str
    condition: str
    threshold: float
    comparison: str  # "gt", "lt", "eq", "gte", "lte" 
    duration: int = 0
    severity: str = "warning"
    description: str
    enabled: bool = True


@monitoring_router.get("/dashboard")
async def get_dashboard():
    """Get comprehensive monitoring dashboard data"""
    try:
        dashboard_data = monitoring_system.get_dashboard_data()
        return {
            "status": "success",
            "data": dashboard_data,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@monitoring_router.get("/metrics/{metric_name}")
async def get_metric_data(metric_name: str, since: Optional[float] = None, limit: int = 100):
    """Get specific metric data points"""
    try:
        points = monitoring_system.metrics_collector.get_metric_values(metric_name, since)
        
        # Limit results
        if limit > 0:
            points = points[-limit:]
        
        return {
            "metric_name": metric_name,
            "data_points": [
                {
                    "timestamp": point.timestamp,
                    "value": point.value,
                    "labels": point.labels
                }
                for point in points
            ],
            "count": len(points)
        }
    except Exception as e:
        logger.error(f"Failed to get metric data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric data: {str(e)}")


@monitoring_router.get("/metrics")
async def list_metrics():
    """List all available metrics"""
    try:
        available_metrics = list(monitoring_system.metrics_collector.metrics.keys())
        
        metric_summary = {}
        for metric in available_metrics:
            latest_value = monitoring_system.metrics_collector.get_latest_value(metric)
            metric_summary[metric] = {
                "latest_value": latest_value,
                "data_points": len(monitoring_system.metrics_collector.metrics[metric])
            }
        
        return {
            "available_metrics": available_metrics,
            "metric_summary": metric_summary,
            "total_metrics": len(available_metrics)
        }
    except Exception as e:
        logger.error(f"Failed to list metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list metrics: {str(e)}")


@monitoring_router.get("/alerts")
async def get_alerts():
    """Get all alert rules and their status"""
    try:
        all_alerts = {}
        active_alerts = monitoring_system.alert_manager.get_active_alerts()
        
        for name, alert in monitoring_system.alert_manager.alerts.items():
            all_alerts[name] = {
                "name": alert.name,
                "condition": alert.condition,
                "threshold": alert.threshold,
                "comparison": alert.comparison,
                "duration": alert.duration,
                "severity": alert.severity,
                "description": alert.description,
                "enabled": alert.enabled,
                "triggered_at": alert.triggered_at,
                "resolved_at": alert.resolved_at,
                "is_active": any(a["name"] == name for a in active_alerts)
            }
        
        return {
            "all_alerts": all_alerts,
            "active_alerts": active_alerts,
            "total_alerts": len(all_alerts),
            "active_count": len(active_alerts)
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@monitoring_router.post("/alerts")
async def create_alert(request: AlertRequest):
    """Create a new alert rule"""
    try:
        alert = Alert(
            name=request.name,
            condition=request.condition,
            threshold=request.threshold,
            comparison=request.comparison,
            duration=request.duration,
            severity=request.severity,
            description=request.description,
            enabled=request.enabled
        )
        
        monitoring_system.alert_manager.add_alert(alert)
        
        return {
            "status": "success",
            "message": f"Alert rule '{request.name}' created successfully",
            "alert": {
                "name": alert.name,
                "condition": alert.condition,
                "threshold": alert.threshold,
                "severity": alert.severity
            }
        }
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@monitoring_router.put("/alerts/{alert_name}/enable")
async def enable_alert(alert_name: str):
    """Enable an alert rule"""
    try:
        if alert_name not in monitoring_system.alert_manager.alerts:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_name}")
        
        monitoring_system.alert_manager.alerts[alert_name].enabled = True
        
        return {
            "status": "success",
            "message": f"Alert '{alert_name}' enabled",
            "alert_name": alert_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable alert: {str(e)}")


@monitoring_router.put("/alerts/{alert_name}/disable")
async def disable_alert(alert_name: str):
    """Disable an alert rule"""
    try:
        if alert_name not in monitoring_system.alert_manager.alerts:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_name}")
        
        monitoring_system.alert_manager.alerts[alert_name].enabled = False
        
        return {
            "status": "success",
            "message": f"Alert '{alert_name}' disabled",
            "alert_name": alert_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable alert: {str(e)}")


@monitoring_router.delete("/alerts/{alert_name}")
async def delete_alert(alert_name: str):
    """Delete an alert rule"""
    try:
        if alert_name not in monitoring_system.alert_manager.alerts:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_name}")
        
        monitoring_system.alert_manager.remove_alert(alert_name)
        
        return {
            "status": "success",
            "message": f"Alert '{alert_name}' deleted",
            "alert_name": alert_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")


@monitoring_router.get("/system")
async def get_system_metrics():
    """Get current system metrics"""
    try:
        # Force collection of current system metrics
        monitoring_system.system_collector.collect_system_metrics()
        
        system_data = {
            "cpu": {
                "usage_percent": monitoring_system.metrics_collector.get_latest_value("system_cpu_percent"),
                "count": monitoring_system.metrics_collector.get_latest_value("system_cpu_count")
            },
            "memory": {
                "total_bytes": monitoring_system.metrics_collector.get_latest_value("system_memory_total_bytes"),
                "used_bytes": monitoring_system.metrics_collector.get_latest_value("system_memory_used_bytes"),
                "usage_percent": monitoring_system.metrics_collector.get_latest_value("system_memory_percent"),
                "available_bytes": monitoring_system.metrics_collector.get_latest_value("system_memory_available_bytes")
            },
            "disk": {
                "total_bytes": monitoring_system.metrics_collector.get_latest_value("system_disk_total_bytes"),
                "used_bytes": monitoring_system.metrics_collector.get_latest_value("system_disk_used_bytes"),
                "usage_percent": monitoring_system.metrics_collector.get_latest_value("system_disk_percent")
            },
            "process": {
                "cpu_percent": monitoring_system.metrics_collector.get_latest_value("process_cpu_percent"),
                "memory_rss_bytes": monitoring_system.metrics_collector.get_latest_value("process_memory_rss_bytes"),
                "memory_vms_bytes": monitoring_system.metrics_collector.get_latest_value("process_memory_vms_bytes"),
                "open_files": monitoring_system.metrics_collector.get_latest_value("process_open_files"),
                "connections": monitoring_system.metrics_collector.get_latest_value("process_connections")
            }
        }
        
        return {
            "timestamp": time.time(),
            "system_metrics": system_data
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@monitoring_router.get("/performance")
async def get_performance_summary():
    """Get performance metrics summary"""
    try:
        performance_data = {
            "requests": {
                "total": monitoring_system.metrics_collector.get_latest_value("counter_http_requests_total") or 0,
                "errors": monitoring_system.metrics_collector.get_latest_value("counter_http_errors_total") or 0,
                "avg_duration": monitoring_system.metrics_collector.get_latest_value("histogram_http_request_duration_seconds_p50"),
                "p95_duration": monitoring_system.metrics_collector.get_latest_value("histogram_http_request_duration_seconds_p95"),
                "p99_duration": monitoring_system.metrics_collector.get_latest_value("histogram_http_request_duration_seconds_p99")
            },
            "rag_queries": {
                "total": monitoring_system.metrics_collector.get_latest_value("counter_rag_queries_total") or 0,
                "avg_duration": monitoring_system.metrics_collector.get_latest_value("histogram_rag_query_duration_seconds_p50"),
                "p95_duration": monitoring_system.metrics_collector.get_latest_value("histogram_rag_query_duration_seconds_p95")
            },
            "vector_search": {
                "avg_duration": monitoring_system.metrics_collector.get_latest_value("vector_search_duration_seconds"),
                "avg_similarity": monitoring_system.metrics_collector.get_latest_value("vector_search_avg_similarity"),
                "max_similarity": monitoring_system.metrics_collector.get_latest_value("vector_search_max_similarity")
            },
            "ai_services": {
                "total_calls": monitoring_system.metrics_collector.get_latest_value("counter_ai_service_calls_total") or 0,
                "avg_duration": monitoring_system.metrics_collector.get_latest_value("histogram_ai_service_duration_seconds_p50"),
                "tokens_used": monitoring_system.metrics_collector.get_latest_value("ai_service_tokens_used")
            }
        }
        
        return {
            "timestamp": time.time(),
            "performance_summary": performance_data
        }
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")


@monitoring_router.get("/export")
async def export_metrics(format: str = "json"):
    """Export all metrics data"""
    try:
        exported_data = monitoring_system.export_metrics(format)
        
        return {
            "format": format,
            "timestamp": time.time(),
            "data": exported_data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export metrics: {str(e)}")


@monitoring_router.post("/start")
async def start_monitoring_system():
    """Start the monitoring system"""
    try:
        monitoring_system.start_monitoring()
        
        return {
            "status": "success",
            "message": "Monitoring system started successfully",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@monitoring_router.post("/stop")
async def stop_monitoring_system():
    """Stop the monitoring system"""
    try:
        monitoring_system.stop_monitoring()
        
        return {
            "status": "success",
            "message": "Monitoring system stopped successfully",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")


@monitoring_router.get("/health")
async def monitoring_health_check():
    """Check monitoring system health"""
    try:
        dashboard_data = monitoring_system.get_dashboard_data()
        active_alerts = monitoring_system.alert_manager.get_active_alerts()
        
        # Determine overall health
        critical_alerts = [a for a in active_alerts if a["severity"] == "critical"]
        
        health_status = "healthy"
        if critical_alerts:
            health_status = "critical"
        elif active_alerts:
            health_status = "warning"
        
        return {
            "status": health_status,
            "monitoring_active": monitoring_system.collecting,
            "alert_evaluation_active": monitoring_system.alert_manager.evaluating,
            "metrics_collected": len(monitoring_system.metrics_collector.metrics),
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "last_collection": dashboard_data.get("timestamp"),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }