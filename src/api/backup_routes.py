"""
Backup and restore API endpoints for HealthAI RAG Application
Provides REST endpoints for backup management and disaster recovery
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
from datetime import datetime

from ..backup.backup_manager import backup_manager

logger = logging.getLogger(__name__)

# Create backup router
backup_router = APIRouter(prefix="/backup", tags=["backup"])


class BackupRequest(BaseModel):
    """Request model for creating backups"""
    compress: bool = True
    verify_integrity: bool = True


class RestoreRequest(BaseModel):
    """Request model for restoring from backup"""
    backup_name: str
    components: Optional[List[str]] = None  # ["vector_store", "documents", "configuration"]
    force: bool = False


class BackupResponse(BaseModel):
    """Response model for backup operations"""
    status: str
    backup_name: Optional[str] = None
    backup_path: Optional[str] = None
    timestamp: str
    message: str
    total_files: Optional[int] = None
    total_size_mb: Optional[float] = None


class BackupListResponse(BaseModel):
    """Response model for listing backups"""
    backups: List[Dict[str, Any]]
    total_count: int
    total_size_mb: float
    scheduler_running: bool


@backup_router.get("/", response_model=BackupListResponse)
async def list_backups():
    """List all available backups with status information"""
    try:
        status = backup_manager.get_backup_status()
        
        total_size_mb = sum(backup.get("size_mb", 0) for backup in status.get("backups", []))
        
        return BackupListResponse(
            backups=status.get("backups", []),
            total_count=len(status.get("backups", [])),
            total_size_mb=total_size_mb,
            scheduler_running=status.get("scheduler_running", False)
        )
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@backup_router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks
):
    """Create a new backup of all components"""
    try:
        # Update configuration based on request
        original_config = backup_manager.config.copy()
        backup_manager.config.update({
            "compress": request.compress,
            "verify_integrity": request.verify_integrity
        })
        
        # Create backup in background
        result = backup_manager.create_full_backup()
        
        # Restore original configuration
        backup_manager.config = original_config
        
        if result["status"] == "success":
            return BackupResponse(
                status="success",
                backup_name=result.get("backup_name"),
                backup_path=result.get("backup_path"),
                timestamp=result.get("timestamp"),
                message="Backup created successfully",
                total_files=result.get("total_files"),
                total_size_mb=result.get("total_size_mb")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Backup failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")


@backup_router.post("/validate/{backup_name}")
async def validate_backup(backup_name: str):
    """Validate backup integrity and completeness"""
    try:
        # Find backup path
        backup_path = None
        status = backup_manager.get_backup_status()
        
        for backup in status.get("backups", []):
            if backup["name"] == backup_name:
                backup_path = Path(backup["path"])
                break
        
        if not backup_path:
            raise HTTPException(status_code=404, detail=f"Backup not found: {backup_name}")
        
        # Validate backup
        validation_result = backup_manager.validate_backup(backup_path)
        
        return {
            "backup_name": backup_name,
            "validation_status": validation_result["status"],
            "timestamp": validation_result["timestamp"],
            "checks": validation_result.get("checks", {}),
            "backup_timestamp": validation_result.get("backup_timestamp"),
            "error": validation_result.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate backup: {str(e)}")


@backup_router.post("/restore", response_model=BackupResponse)
async def restore_backup(request: RestoreRequest):
    """Restore system from backup"""
    try:
        # Find backup path
        backup_path = None
        status = backup_manager.get_backup_status()
        
        for backup in status.get("backups", []):
            if backup["name"] == request.backup_name:
                backup_path = Path(backup["path"])
                break
        
        if not backup_path:
            raise HTTPException(status_code=404, detail=f"Backup not found: {request.backup_name}")
        
        # Validate backup before restore if not forced
        if not request.force:
            validation_result = backup_manager.validate_backup(backup_path)
            if validation_result["status"] != "passed":
                raise HTTPException(
                    status_code=400,
                    detail="Backup validation failed. Use force=true to override."
                )
        
        # Perform restore
        restore_result = backup_manager.restore_from_backup(backup_path, request.components)
        
        if restore_result["status"] == "success":
            return BackupResponse(
                status="success",
                backup_name=request.backup_name,
                timestamp=restore_result.get("timestamp"),
                message=f"Restore completed. Components: {restore_result.get('restored_components', [])}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Restore failed: {restore_result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restore backup: {str(e)}")


@backup_router.delete("/cleanup")
async def cleanup_old_backups():
    """Remove backups older than retention period"""
    try:
        cleanup_result = backup_manager.cleanup_old_backups()
        
        if cleanup_result["status"] == "success":
            return {
                "status": "success",
                "removed_count": cleanup_result["removed_count"],
                "freed_space_mb": cleanup_result["freed_space_mb"],
                "errors": cleanup_result.get("errors", []),
                "timestamp": datetime.now().isoformat(),
                "message": f"Cleaned up {cleanup_result['removed_count']} old backups"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Cleanup failed: {cleanup_result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Failed to cleanup backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup backups: {str(e)}")


@backup_router.post("/schedule/start")
async def start_scheduled_backups(backup_time: str = "02:00"):
    """Start scheduled backup service"""
    try:
        backup_manager.start_scheduled_backups(backup_time)
        
        return {
            "status": "success",
            "message": f"Scheduled backups started - daily at {backup_time}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start scheduled backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduled backups: {str(e)}")


@backup_router.post("/schedule/stop")
async def stop_scheduled_backups():
    """Stop scheduled backup service"""
    try:
        backup_manager.stop_scheduled_backups()
        
        return {
            "status": "success",
            "message": "Scheduled backups stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop scheduled backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduled backups: {str(e)}")


@backup_router.get("/status")
async def get_backup_system_status():
    """Get comprehensive backup system status"""
    try:
        status = backup_manager.get_backup_status()
        
        return {
            "backup_system": {
                "scheduler_running": status.get("scheduler_running", False),
                "backup_root": status.get("backup_root"),
                "retention_days": status.get("retention_days"),
                "configuration": status.get("config", {})
            },
            "backups": {
                "total_count": len(status.get("backups", [])),
                "total_size_mb": sum(backup.get("size_mb", 0) for backup in status.get("backups", [])),
                "recent_backups": status.get("backups", [])[-5:]  # Last 5 backups
            },
            "health": {
                "status": "healthy" if not status.get("error") else "error",
                "error": status.get("error"),
                "last_check": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get backup status: {str(e)}")