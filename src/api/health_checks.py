"""
Production health check endpoints for HealthAI RAG Application
Implements /healthz and /readyz endpoints with comprehensive dependency monitoring
"""

import asyncio
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List
from fastapi import HTTPException, Response
import logging

logger = logging.getLogger(__name__)


class HealthCheckManager:
    """Comprehensive health check manager for production monitoring"""
    
    def __init__(self):
        self.startup_time = time.time()
        self.last_health_check = None
        self.health_status = {}
        
    async def check_ai_services(self) -> Dict[str, Any]:
        """Check AI service availability and performance"""
        from src.api.app import gemini_client, groq_client
        
        ai_status = {
            "gemini": {"status": "unknown", "response_time": None, "error": None},
            "groq": {"status": "unknown", "response_time": None, "error": None}
        }
        
        # Check Gemini service
        if gemini_client:
            try:
                start_time = time.time()
                # Quick health check query
                response = gemini_client.generate_content("health check")
                response_time = time.time() - start_time
                
                if hasattr(response, 'text') and response.text:
                    ai_status["gemini"] = {
                        "status": "healthy",
                        "response_time": response_time,
                        "error": None
                    }
                else:
                    ai_status["gemini"]["status"] = "unhealthy"
                    ai_status["gemini"]["error"] = "No response text"
                    
            except Exception as e:
                ai_status["gemini"] = {
                    "status": "unhealthy", 
                    "response_time": None,
                    "error": str(e)
                }
        else:
            ai_status["gemini"]["status"] = "not_configured"
        
        # Check Groq service
        if groq_client:
            try:
                start_time = time.time()
                response = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": "health check"}],
                    model="mixtral-8x7b-32768",
                    max_tokens=10,
                    temperature=0
                )
                response_time = time.time() - start_time
                
                if response.choices and response.choices[0].message.content:
                    ai_status["groq"] = {
                        "status": "healthy",
                        "response_time": response_time,
                        "error": None
                    }
                else:
                    ai_status["groq"]["status"] = "unhealthy"
                    ai_status["groq"]["error"] = "No response content"
                    
            except Exception as e:
                ai_status["groq"] = {
                    "status": "unhealthy",
                    "response_time": None, 
                    "error": str(e)
                }
        else:
            ai_status["groq"]["status"] = "not_configured"
        
        return ai_status
    
    def check_vector_store(self) -> Dict[str, Any]:
        """Check vector store health and accessibility"""
        vector_status = {
            "status": "unknown",
            "path_exists": False,
            "readable": False,
            "file_count": 0,
            "total_size_mb": 0,
            "error": None
        }
        
        try:
            from src.vectorstore.faiss_store import FAISSVectorStore
            
            # Check vectorstore directory
            vectorstore_path = Path("data/vectorstore")
            vector_status["path_exists"] = vectorstore_path.exists()
            
            if vectorstore_path.exists():
                vector_status["readable"] = vectorstore_path.is_dir()
                
                # Count files and calculate size
                files = list(vectorstore_path.glob("*"))
                vector_status["file_count"] = len(files)
                vector_status["total_size_mb"] = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
                
                # Try to initialize vector store
                try:
                    temp_vs = FAISSVectorStore(dimension=384)
                    stats = temp_vs.get_stats()
                    vector_status["status"] = "healthy"
                    vector_status["documents"] = stats.get("total_documents", 0)
                except Exception as e:
                    vector_status["status"] = "unhealthy"
                    vector_status["error"] = f"Initialization failed: {str(e)}"
            else:
                vector_status["status"] = "unhealthy"
                vector_status["error"] = "Vectorstore directory does not exist"
                
        except Exception as e:
            vector_status["status"] = "unhealthy"
            vector_status["error"] = f"Check failed: {str(e)}"
        
        return vector_status
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total_mb": memory.total / (1024 * 1024),
                    "available_mb": memory.available / (1024 * 1024),
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024 * 1024 * 1024),
                    "free_gb": disk.free / (1024 * 1024 * 1024),
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "uptime_seconds": time.time() - self.startup_time
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies and network connectivity"""
        dependencies = {
            "status": "healthy",
            "checks": {}
        }
        
        # Check critical Python packages
        critical_packages = ["fastapi", "numpy", "faiss-cpu", "openai"]
        for package in critical_packages:
            try:
                __import__(package.replace("-", "_"))
                dependencies["checks"][package] = {"status": "available"}
            except ImportError:
                dependencies["checks"][package] = {"status": "missing"}
                dependencies["status"] = "unhealthy"
        
        # Check data directories
        data_dirs = ["data", "data/pdfs", "data/vectorstore"]
        for dir_path in data_dirs:
            path = Path(dir_path)
            dependencies["checks"][f"dir_{dir_path}"] = {
                "status": "exists" if path.exists() else "missing",
                "readable": path.is_dir() if path.exists() else False
            }
        
        return dependencies
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all components"""
        start_time = time.time()
        
        # Run all health checks
        health_results = {
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.startup_time,
            "checks": {}
        }
        
        try:
            # System resources (fast check)
            health_results["checks"]["system"] = self.check_system_resources()
            
            # Dependencies (fast check)
            health_results["checks"]["dependencies"] = self.check_dependencies()
            
            # Vector store (medium speed check)
            health_results["checks"]["vector_store"] = self.check_vector_store()
            
            # AI services (slow check - may timeout)
            try:
                ai_check = await asyncio.wait_for(
                    self.check_ai_services(), 
                    timeout=10.0  # 10 second timeout
                )
                health_results["checks"]["ai_services"] = ai_check
            except asyncio.TimeoutError:
                health_results["checks"]["ai_services"] = {
                    "status": "timeout",
                    "error": "Health check timed out after 10 seconds"
                }
            
            # Calculate overall status
            all_checks = []
            for check_name, check_result in health_results["checks"].items():
                if isinstance(check_result, dict):
                    if check_name == "ai_services":
                        # For AI services, check individual service status
                        for service_name, service_status in check_result.items():
                            if isinstance(service_status, dict):
                                all_checks.append(service_status.get("status", "unknown"))
                    else:
                        all_checks.append(check_result.get("status", "unknown"))
            
            # Determine overall health
            if all(status in ["healthy", "not_configured"] for status in all_checks):
                health_results["status"] = "healthy"
            elif any(status == "unhealthy" for status in all_checks):
                health_results["status"] = "unhealthy" 
            else:
                health_results["status"] = "degraded"
            
        except Exception as e:
            health_results["status"] = "unhealthy"
            health_results["error"] = str(e)
        
        health_results["check_duration_seconds"] = time.time() - start_time
        self.last_health_check = health_results
        
        return health_results


# Global health check manager instance
health_manager = HealthCheckManager()


async def healthz_endpoint() -> Dict[str, Any]:
    """
    Kubernetes-style liveness probe endpoint
    Fast, basic health check to determine if the application is alive
    """
    try:
        # Quick system check
        system_status = health_manager.check_system_resources()
        
        basic_health = {
            "status": "healthy" if system_status["status"] == "healthy" else "unhealthy",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - health_manager.startup_time,
            "service": "healthai-rag",
            "version": "1.0.0"
        }
        
        # Add memory and CPU status for quick assessment
        if system_status["status"] == "healthy":
            basic_health["resources"] = {
                "memory_usage_percent": system_status["memory"]["usage_percent"],
                "cpu_usage_percent": system_status["cpu"]["usage_percent"]
            }
        
        return basic_health
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e),
            "service": "healthai-rag"
        }


async def readyz_endpoint() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe endpoint  
    Comprehensive check to determine if application is ready to serve traffic
    """
    try:
        # Perform comprehensive health check
        health_results = await health_manager.perform_comprehensive_health_check()
        
        # Determine readiness based on critical components
        critical_components = ["system", "dependencies", "vector_store"]
        readiness_checks = {}
        
        for component in critical_components:
            if component in health_results["checks"]:
                check_result = health_results["checks"][component]
                readiness_checks[component] = {
                    "status": check_result.get("status", "unknown"),
                    "ready": check_result.get("status") == "healthy"
                }
            else:
                readiness_checks[component] = {"status": "unknown", "ready": False}
        
        # Application is ready if all critical components are healthy
        all_ready = all(check["ready"] for check in readiness_checks.values())
        
        readiness_response = {
            "status": "ready" if all_ready else "not_ready",
            "timestamp": time.time(),
            "service": "healthai-rag",
            "checks": readiness_checks,
            "overall_health": health_results["status"]
        }
        
        # Include AI service status (non-critical for readiness)
        if "ai_services" in health_results["checks"]:
            ai_status = health_results["checks"]["ai_services"]
            readiness_response["ai_services_available"] = any(
                service.get("status") == "healthy" 
                for service in ai_status.values()
                if isinstance(service, dict)
            )
        
        return readiness_response
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "timestamp": time.time(),
            "error": str(e),
            "service": "healthai-rag"
        }


async def health_detailed_endpoint() -> Dict[str, Any]:
    """
    Detailed health check endpoint for monitoring and debugging
    Provides comprehensive system status information
    """
    try:
        health_results = await health_manager.perform_comprehensive_health_check()
        
        # Add additional metadata for monitoring
        health_results.update({
            "service": "healthai-rag",
            "version": "1.0.0",
            "environment": "production",  # Could be configured via env var
            "last_check_cached": health_manager.last_health_check is not None
        })
        
        return health_results
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e),
            "service": "healthai-rag",
            "checks": {}
        }


def get_health_status_code(health_data: Dict[str, Any]) -> int:
    """Get appropriate HTTP status code based on health status"""
    status = health_data.get("status", "unknown")
    
    if status in ["healthy", "ready"]:
        return 200
    elif status in ["degraded"]:
        return 200  # Still serving traffic but with warnings
    elif status in ["not_ready"]:
        return 503  # Service unavailable
    else:  # unhealthy, unknown
        return 503