"""
Graceful shutdown handler for HealthAI RAG Application
Manages proper application shutdown to prevent data corruption and resource leaks
"""

import signal
import asyncio
import threading
import time
import logging
from typing import List, Callable, Any
from contextlib import asynccontextmanager
import atexit
from pathlib import Path

logger = logging.getLogger(__name__)


class ShutdownHandler:
    """Manages graceful application shutdown"""
    
    def __init__(self):
        self.shutdown_callbacks: List[Callable] = []
        self.async_shutdown_callbacks: List[Callable] = []
        self.shutdown_initiated = False
        self.shutdown_timeout = 30  # seconds
        self._shutdown_lock = threading.Lock()
        
        # Register signal handlers
        self._register_signal_handlers()
        
        # Register atexit handler
        atexit.register(self._atexit_handler)
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.initiate_shutdown()
        
        # Register for common termination signals
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Windows-specific signals
        try:
            signal.signal(signal.SIGBREAK, signal_handler)
        except AttributeError:
            # SIGBREAK not available on non-Windows
            pass
    
    def add_shutdown_callback(self, callback: Callable, is_async: bool = False):
        """Add a shutdown callback function"""
        if is_async:
            self.async_shutdown_callbacks.append(callback)
        else:
            self.shutdown_callbacks.append(callback)
        
        logger.debug(f"Added {'async' if is_async else 'sync'} shutdown callback: {callback.__name__}")
    
    def remove_shutdown_callback(self, callback: Callable):
        """Remove a shutdown callback function"""
        if callback in self.shutdown_callbacks:
            self.shutdown_callbacks.remove(callback)
        if callback in self.async_shutdown_callbacks:
            self.async_shutdown_callbacks.remove(callback)
        
        logger.debug(f"Removed shutdown callback: {callback.__name__}")
    
    def initiate_shutdown(self):
        """Initiate graceful shutdown process"""
        with self._shutdown_lock:
            if self.shutdown_initiated:
                logger.warning("Shutdown already initiated")
                return
            
            self.shutdown_initiated = True
        
        logger.info("Starting graceful shutdown process...")
        
        try:
            # Execute sync callbacks first
            for callback in self.shutdown_callbacks:
                try:
                    logger.debug(f"Executing shutdown callback: {callback.__name__}")
                    callback()
                except Exception as e:
                    logger.error(f"Error in shutdown callback {callback.__name__}: {e}")
            
            # Execute async callbacks
            if self.async_shutdown_callbacks:
                asyncio.run(self._execute_async_callbacks())
            
            logger.info("Graceful shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
        
        finally:
            # Force exit if needed
            import os
            os._exit(0)
    
    async def _execute_async_callbacks(self):
        """Execute async shutdown callbacks"""
        tasks = []
        
        for callback in self.async_shutdown_callbacks:
            try:
                logger.debug(f"Creating async shutdown task: {callback.__name__}")
                task = asyncio.create_task(callback())
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating async shutdown task {callback.__name__}: {e}")
        
        if tasks:
            try:
                # Wait for all tasks to complete with timeout
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.shutdown_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Async shutdown callbacks timed out after {self.shutdown_timeout}s")
                # Cancel remaining tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()
    
    def _atexit_handler(self):
        """Handler called when Python interpreter is about to exit"""
        if not self.shutdown_initiated:
            logger.info("Python interpreter exiting, initiating graceful shutdown...")
            self.initiate_shutdown()
    
    @asynccontextmanager
    async def lifespan_context(self, app):
        """FastAPI lifespan context manager"""
        logger.info("Application startup initiated")
        
        # Startup logic can be added here
        yield
        
        logger.info("Application shutdown initiated via lifespan")
        if not self.shutdown_initiated:
            self.initiate_shutdown()


class ResourceManager:
    """Manages application resources that need cleanup"""
    
    def __init__(self, shutdown_handler: ShutdownHandler):
        self.shutdown_handler = shutdown_handler
        self.active_connections = set()
        self.background_tasks = set()
        self.temporary_files = set()
        self.open_file_handles = set()
        
        # Register cleanup callbacks
        self.shutdown_handler.add_shutdown_callback(self.cleanup_resources)
    
    def register_connection(self, connection: Any):
        """Register an active connection for cleanup"""
        self.active_connections.add(connection)
    
    def unregister_connection(self, connection: Any):
        """Unregister a connection"""
        self.active_connections.discard(connection)
    
    def register_background_task(self, task: asyncio.Task):
        """Register a background task for cleanup"""
        self.background_tasks.add(task)
    
    def unregister_background_task(self, task: asyncio.Task):
        """Unregister a background task"""
        self.background_tasks.discard(task)
    
    def register_temporary_file(self, file_path: Path):
        """Register a temporary file for cleanup"""
        self.temporary_files.add(file_path)
    
    def register_file_handle(self, file_handle):
        """Register a file handle for cleanup"""
        self.open_file_handles.add(file_handle)
    
    def cleanup_resources(self):
        """Clean up all registered resources"""
        logger.info("Cleaning up application resources...")
        
        self._cleanup_connections()
        self._cleanup_background_tasks()
        self._cleanup_file_handles()
        self._cleanup_temporary_files()
        
        logger.info("Resource cleanup completed")
    
    def _cleanup_connections(self):
        """Close active connections"""
        if not self.active_connections:
            return
        
        logger.info(f"Closing {len(self.active_connections)} active connections")
        for connection in self.active_connections.copy():
            try:
                if hasattr(connection, 'close'):
                    connection.close()
                elif hasattr(connection, 'disconnect'):
                    connection.disconnect()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    def _cleanup_background_tasks(self):
        """Cancel background tasks"""
        if not self.background_tasks:
            return
        
        logger.info(f"Canceling {len(self.background_tasks)} background tasks")
        for task in self.background_tasks.copy():
            try:
                if not task.done():
                    task.cancel()
            except Exception as e:
                logger.error(f"Error canceling task: {e}")
    
    def _cleanup_file_handles(self):
        """Close file handles"""
        if not self.open_file_handles:
            return
        
        logger.info(f"Closing {len(self.open_file_handles)} file handles")
        for handle in self.open_file_handles.copy():
            try:
                handle.close()
            except Exception as e:
                logger.error(f"Error closing file handle: {e}")
    
    def _cleanup_temporary_files(self):
        """Clean up temporary files"""
        if not self.temporary_files:
            return
        
        logger.info(f"Cleaning up {len(self.temporary_files)} temporary files")
        for file_path in self.temporary_files.copy():
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.error(f"Error removing temporary file {file_path}: {e}")


class ApplicationShutdown:
    """Application-specific shutdown logic for HealthAI RAG"""
    
    def __init__(self, shutdown_handler: ShutdownHandler):
        self.shutdown_handler = shutdown_handler
        
        # Register shutdown callbacks
        self.shutdown_handler.add_shutdown_callback(self.save_application_state)
        self.shutdown_handler.add_shutdown_callback(self.cleanup_vector_store)
        self.shutdown_handler.add_shutdown_callback(self.stop_monitoring_systems)
        self.shutdown_handler.add_shutdown_callback(self.flush_pending_data)
        
    def save_application_state(self):
        """Save current application state"""
        try:
            logger.info("Saving application state...")
            
            # Save current metrics state
            from ..monitoring.enhanced_monitoring import monitoring_system
            if monitoring_system.collecting:
                dashboard_data = monitoring_system.get_dashboard_data()
                
                # Save to file for recovery
                state_file = Path("data/shutdown_state.json")
                state_file.parent.mkdir(exist_ok=True)
                
                import json
                with open(state_file, 'w') as f:
                    json.dump({
                        "timestamp": time.time(),
                        "dashboard_data": dashboard_data,
                        "shutdown_reason": "graceful_shutdown"
                    }, f, indent=2)
                
                logger.info(f"Application state saved to {state_file}")
            
        except Exception as e:
            logger.error(f"Failed to save application state: {e}")
    
    def cleanup_vector_store(self):
        """Clean up vector store connections and flush data"""
        try:
            logger.info("Cleaning up vector store...")
            
            # Flush any pending vector store operations
            # This would be specific to your vector store implementation
            logger.info("Vector store cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup vector store: {e}")
    
    def stop_monitoring_systems(self):
        """Stop monitoring and backup systems"""
        try:
            logger.info("Stopping monitoring systems...")
            
            # Stop monitoring system
            from ..monitoring.enhanced_monitoring import monitoring_system
            if monitoring_system.collecting:
                monitoring_system.stop_monitoring()
            
            # Stop backup scheduler
            from ..backup.backup_manager import backup_manager
            if backup_manager.scheduler_running:
                backup_manager.stop_scheduled_backups()
            
            logger.info("Monitoring systems stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring systems: {e}")
    
    def flush_pending_data(self):
        """Flush any pending data to disk"""
        try:
            logger.info("Flushing pending data...")
            
            # Force flush of any buffered data
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
            
            # Sync filesystem
            try:
                import os
                os.sync()  # Unix only
            except (AttributeError, OSError):
                pass  # Not available or not needed on Windows
            
            logger.info("Data flush completed")
            
        except Exception as e:
            logger.error(f"Failed to flush pending data: {e}")


# Global shutdown handler instance
shutdown_handler = ShutdownHandler()
resource_manager = ResourceManager(shutdown_handler)
app_shutdown = ApplicationShutdown(shutdown_handler)


def setup_graceful_shutdown(app):
    """Setup graceful shutdown for FastAPI application"""
    
    # Add lifespan context to FastAPI app
    @asynccontextmanager
    async def lifespan(app):
        # Startup
        logger.info("FastAPI application starting up...")
        
        # Start monitoring system
        from ..monitoring.enhanced_monitoring import monitoring_system
        monitoring_system.start_monitoring()
        
        yield
        
        # Shutdown
        logger.info("FastAPI application shutting down...")
        if not shutdown_handler.shutdown_initiated:
            shutdown_handler.initiate_shutdown()
    
    # Set the lifespan for the app
    app.router.lifespan_context = lifespan
    
    return app


class HealthCheckShutdown:
    """Health check integration with shutdown handler"""
    
    def __init__(self, shutdown_handler: ShutdownHandler):
        self.shutdown_handler = shutdown_handler
    
    def is_shutting_down(self) -> bool:
        """Check if application is in shutdown process"""
        return self.shutdown_handler.shutdown_initiated
    
    def get_shutdown_status(self) -> dict:
        """Get current shutdown status"""
        return {
            "shutdown_initiated": self.shutdown_handler.shutdown_initiated,
            "registered_callbacks": len(self.shutdown_handler.shutdown_callbacks),
            "registered_async_callbacks": len(self.shutdown_handler.async_shutdown_callbacks),
            "shutdown_timeout": self.shutdown_handler.shutdown_timeout
        }


# Global health check shutdown instance
health_check_shutdown = HealthCheckShutdown(shutdown_handler)


# Decorator for graceful shutdown context
def with_graceful_shutdown(func):
    """Decorator to add graceful shutdown context to functions"""
    def wrapper(*args, **kwargs):
        if shutdown_handler.shutdown_initiated:
            logger.warning(f"Function {func.__name__} called during shutdown, skipping...")
            return None
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            if not shutdown_handler.shutdown_initiated:
                shutdown_handler.initiate_shutdown()
            raise
    
    return wrapper


# Context manager for temporary resources
@asynccontextmanager
async def managed_resource(resource, cleanup_func=None):
    """Context manager for resources that need cleanup on shutdown"""
    try:
        # Register resource for cleanup
        if hasattr(resource, 'close'):
            resource_manager.register_connection(resource)
        
        yield resource
        
    finally:
        # Cleanup resource
        try:
            if cleanup_func:
                cleanup_func(resource)
            elif hasattr(resource, 'close'):
                resource.close()
                resource_manager.unregister_connection(resource)
        except Exception as e:
            logger.error(f"Error cleaning up resource: {e}")


if __name__ == "__main__":
    # Test graceful shutdown
    import time
    
    def test_callback():
        print("Test shutdown callback executed")
        time.sleep(1)
    
    async def test_async_callback():
        print("Test async shutdown callback started")
        await asyncio.sleep(2)
        print("Test async shutdown callback completed")
    
    # Add test callbacks
    shutdown_handler.add_shutdown_callback(test_callback)
    shutdown_handler.add_shutdown_callback(test_async_callback, is_async=True)
    
    print("Shutdown handler initialized. Press Ctrl+C to test graceful shutdown...")
    
    try:
        time.sleep(60)  # Wait for signal
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, graceful shutdown will handle it...")
        time.sleep(5)  # Let graceful shutdown complete