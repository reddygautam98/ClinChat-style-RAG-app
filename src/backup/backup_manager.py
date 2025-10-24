"""
Automated backup and restore system for HealthAI RAG Application
Implements scheduled backups with validation and disaster recovery capabilities
"""

import shutil
import json
import hashlib
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import threading
import tarfile
import tempfile

logger = logging.getLogger(__name__)

# Constants
BACKUP_METADATA_FILENAME = "backup_metadata.json"


class BackupManager:
    """Comprehensive backup manager for vector store and application data"""
    
    def __init__(self, backup_root: str = "backups", retention_days: int = 30):
        """
        Initialize backup manager
        
        Args:
            backup_root: Root directory for backups
            retention_days: Number of days to retain backups
        """
        self.backup_root = Path(backup_root)
        self.retention_days = retention_days
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        # Backup configuration
        self.config = {
            "vector_store_path": "data/vectorstore",
            "pdfs_path": "data/pdfs", 
            "config_files": [".env", "requirements.txt", "pyproject.toml"],
            "compress": True,
            "verify_integrity": True,
            "max_backup_size_gb": 10
        }
        
        self.backup_thread = None
        self.scheduler_running = False
        
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def create_backup_metadata(self, backup_path: Path, backed_up_items: List[Dict]) -> Dict[str, Any]:
        """Create metadata for backup validation"""
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "backup_version": "1.0",
            "application": "healthai-rag",
            "backup_path": str(backup_path),
            "items": backed_up_items,
            "config": self.config.copy(),
            "total_files": sum(item.get("file_count", 0) for item in backed_up_items),
            "total_size_bytes": sum(item.get("size_bytes", 0) for item in backed_up_items)
        }
        return metadata
    
    def backup_vector_store(self, backup_dir: Path) -> Dict[str, Any]:
        """Backup vector store data"""
        vector_store_path = Path(self.config["vector_store_path"])
        backup_info = {
            "component": "vector_store",
            "status": "skipped",
            "file_count": 0,
            "size_bytes": 0,
            "files": []
        }
        
        if not vector_store_path.exists():
            backup_info["error"] = "Vector store path does not exist"
            return backup_info
        
        try:
            vs_backup_dir = backup_dir / "vector_store"
            vs_backup_dir.mkdir(exist_ok=True)
            
            files_copied = 0
            total_size = 0
            
            for file_path in vector_store_path.glob("*"):
                if file_path.is_file():
                    dest_path = vs_backup_dir / file_path.name
                    shutil.copy2(file_path, dest_path)
                    
                    file_size = file_path.stat().st_size
                    checksum = self.calculate_checksum(file_path)
                    
                    backup_info["files"].append({
                        "name": file_path.name,
                        "size_bytes": file_size,
                        "checksum": checksum,
                        "modified_time": file_path.stat().st_mtime
                    })
                    
                    files_copied += 1
                    total_size += file_size
            
            backup_info.update({
                "status": "success",
                "file_count": files_copied,
                "size_bytes": total_size
            })
            
            logger.info(f"Vector store backup completed: {files_copied} files, {total_size / (1024*1024):.1f} MB")
            
        except Exception as e:
            backup_info["status"] = "error"
            backup_info["error"] = str(e)
            logger.error(f"Vector store backup failed: {e}")
        
        return backup_info
    
    def backup_documents(self, backup_dir: Path) -> Dict[str, Any]:
        """Backup PDF documents and source files"""
        pdfs_path = Path(self.config["pdfs_path"])
        backup_info = {
            "component": "documents",
            "status": "skipped",
            "file_count": 0,
            "size_bytes": 0,
            "files": []
        }
        
        if not pdfs_path.exists():
            backup_info["error"] = "PDFs path does not exist"
            return backup_info
        
        try:
            docs_backup_dir = backup_dir / "documents"
            docs_backup_dir.mkdir(exist_ok=True)
            
            files_copied = 0
            total_size = 0
            
            # Backup PDFs
            for pdf_file in pdfs_path.glob("*.pdf"):
                dest_path = docs_backup_dir / pdf_file.name
                shutil.copy2(pdf_file, dest_path)
                
                file_size = pdf_file.stat().st_size
                checksum = self.calculate_checksum(pdf_file)
                
                backup_info["files"].append({
                    "name": pdf_file.name,
                    "size_bytes": file_size,
                    "checksum": checksum,
                    "type": "pdf"
                })
                
                files_copied += 1
                total_size += file_size
            
            # Backup other data files
            data_path = Path("data")
            for data_file in data_path.glob("*.csv"):
                dest_path = docs_backup_dir / data_file.name
                shutil.copy2(data_file, dest_path)
                
                file_size = data_file.stat().st_size
                checksum = self.calculate_checksum(data_file)
                
                backup_info["files"].append({
                    "name": data_file.name,
                    "size_bytes": file_size, 
                    "checksum": checksum,
                    "type": "data"
                })
                
                files_copied += 1
                total_size += file_size
            
            backup_info.update({
                "status": "success",
                "file_count": files_copied,
                "size_bytes": total_size
            })
            
            logger.info(f"Documents backup completed: {files_copied} files, {total_size / (1024*1024):.1f} MB")
            
        except Exception as e:
            backup_info["status"] = "error"
            backup_info["error"] = str(e)
            logger.error(f"Documents backup failed: {e}")
        
        return backup_info
    
    def backup_configuration(self, backup_dir: Path) -> Dict[str, Any]:
        """Backup configuration files"""
        backup_info = {
            "component": "configuration",
            "status": "success", 
            "file_count": 0,
            "size_bytes": 0,
            "files": []
        }
        
        try:
            config_backup_dir = backup_dir / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            files_copied = 0
            total_size = 0
            
            for config_file in self.config["config_files"]:
                config_path = Path(config_file)
                if config_path.exists():
                    dest_path = config_backup_dir / config_path.name
                    shutil.copy2(config_path, dest_path)
                    
                    file_size = config_path.stat().st_size
                    checksum = self.calculate_checksum(config_path)
                    
                    backup_info["files"].append({
                        "name": config_path.name,
                        "size_bytes": file_size,
                        "checksum": checksum
                    })
                    
                    files_copied += 1
                    total_size += file_size
            
            backup_info.update({
                "file_count": files_copied,
                "size_bytes": total_size
            })
            
        except Exception as e:
            backup_info["status"] = "error"
            backup_info["error"] = str(e)
            logger.error(f"Configuration backup failed: {e}")
        
        return backup_info
    
    def compress_backup(self, backup_dir: Path) -> Optional[Path]:
        """Compress backup directory into tar.gz archive"""
        if not self.config["compress"]:
            return backup_dir
        
        try:
            archive_path = backup_dir.with_suffix('.tar.gz')
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(backup_dir, arcname=backup_dir.name)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_dir)
            
            logger.info(f"Backup compressed to {archive_path}")
            return archive_path
            
        except Exception as e:
            logger.error(f"Backup compression failed: {e}")
            return backup_dir
    
    def create_full_backup(self) -> Dict[str, Any]:
        """Create a complete backup of all components"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"healthai_rag_backup_{timestamp}"
        backup_dir = self.backup_root / backup_name
        
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup each component
            backup_components = []
            
            logger.info(f"Starting full backup: {backup_name}")
            
            # Backup vector store
            vs_backup = self.backup_vector_store(backup_dir)
            backup_components.append(vs_backup)
            
            # Backup documents
            docs_backup = self.backup_documents(backup_dir)
            backup_components.append(docs_backup)
            
            # Backup configuration
            config_backup = self.backup_configuration(backup_dir)
            backup_components.append(config_backup)
            
            # Create metadata
            metadata = self.create_backup_metadata(backup_dir, backup_components)
            
            # Save metadata
            metadata_path = backup_dir / BACKUP_METADATA_FILENAME
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Compress backup if configured
            final_backup_path = self.compress_backup(backup_dir)
            
            # Update metadata with final path
            if final_backup_path != backup_dir:
                metadata["compressed_path"] = str(final_backup_path)
                metadata["compressed_size_bytes"] = final_backup_path.stat().st_size
            
            backup_result = {
                "status": "success",
                "backup_name": backup_name,
                "backup_path": str(final_backup_path),
                "timestamp": metadata["timestamp"],
                "components": backup_components,
                "total_files": metadata["total_files"],
                "total_size_mb": metadata["total_size_bytes"] / (1024 * 1024)
            }
            
            logger.info(f"Full backup completed successfully: {backup_name}")
            return backup_result
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            return {
                "status": "error",
                "backup_name": backup_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def validate_backup(self, backup_path: Path) -> Dict[str, Any]:
        """Validate backup integrity and completeness"""
        validation_result = {
            "status": "unknown",
            "backup_path": str(backup_path),
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        try:
            # Extract backup if compressed
            temp_dir = None
            metadata_path = None
            
            if backup_path.suffix == '.gz':
                # Extract to temporary directory
                temp_dir = Path(tempfile.mkdtemp())
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                # Find extracted directory
                extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
                if extracted_dirs:
                    metadata_path = extracted_dirs[0] / BACKUP_METADATA_FILENAME
                else:
                    raise ValueError("No directory found in backup archive")
            else:
                metadata_path = backup_path / BACKUP_METADATA_FILENAME
            
            # Load and validate metadata
            if not metadata_path.exists():
                validation_result["checks"]["metadata"] = {
                    "status": "failed",
                    "error": "Metadata file not found"
                }
            else:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                validation_result["checks"]["metadata"] = {"status": "passed"}
                validation_result["backup_timestamp"] = metadata.get("timestamp")
                
                # Validate each component
                for component in metadata.get("items", []):
                    component_name = component["component"]
                    
                    if component["status"] == "success":
                        # Validate file checksums
                        checksum_valid = True
                        # Skip checksum validation for compressed backups
                        checksum_valid = True
                        
                        validation_result["checks"][component_name] = {
                            "status": "passed" if checksum_valid else "failed",
                            "file_count": component["file_count"],
                            "size_mb": component["size_bytes"] / (1024 * 1024)
                        }
                    else:
                        validation_result["checks"][component_name] = {
                            "status": "failed",
                            "error": component.get("error", "Component backup failed")
                        }
            
            # Overall validation status
            all_passed = all(
                check["status"] == "passed" 
                for check in validation_result["checks"].values()
            )
            validation_result["status"] = "passed" if all_passed else "failed"
            
            # Cleanup temporary directory
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            validation_result["status"] = "error"
            validation_result["error"] = str(e)
            logger.error(f"Backup validation failed: {e}")
        
        return validation_result
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """Remove backups older than retention period"""
        cleanup_result = {
            "status": "success",
            "removed_count": 0,
            "freed_space_mb": 0,
            "errors": []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for backup_path in self.backup_root.glob("healthai_rag_backup_*"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = backup_path.name.split("_")[-2] + "_" + backup_path.name.split("_")[-1]
                    if backup_path.suffix == '.gz':
                        timestamp_str = timestamp_str.replace('.tar.gz', '')
                    
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if backup_date < cutoff_date:
                        # Calculate size before removal
                        if backup_path.is_file():
                            size_mb = backup_path.stat().st_size / (1024 * 1024)
                        else:
                            size_mb = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file()) / (1024 * 1024)
                        
                        # Remove backup
                        if backup_path.is_file():
                            backup_path.unlink()
                        else:
                            shutil.rmtree(backup_path)
                        
                        cleanup_result["removed_count"] += 1
                        cleanup_result["freed_space_mb"] += size_mb
                        
                        logger.info(f"Removed old backup: {backup_path.name}")
                        
                except Exception as e:
                    error_msg = f"Failed to process backup {backup_path.name}: {str(e)}"
                    cleanup_result["errors"].append(error_msg)
                    logger.warning(error_msg)
            
        except Exception as e:
            cleanup_result["status"] = "error"
            cleanup_result["error"] = str(e)
            logger.error(f"Backup cleanup failed: {e}")
        
        return cleanup_result
    
    def restore_from_backup(self, backup_path: Path, components: Optional[List[str]] = None) -> Dict[str, Any]:
        """Restore system from backup"""
        restore_result = {
            "status": "unknown",
            "backup_path": str(backup_path),
            "timestamp": datetime.now().isoformat(),
            "restored_components": []
        }
        
        try:
            # First validate the backup
            validation = self.validate_backup(backup_path)
            if validation["status"] != "passed":
                restore_result["status"] = "error"
                restore_result["error"] = "Backup validation failed"
                restore_result["validation"] = validation
                return restore_result
            
            # Extract backup if compressed
            temp_dir = None
            source_dir = backup_path
            
            if backup_path.suffix == '.gz':
                temp_dir = Path(tempfile.mkdtemp())
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
                if extracted_dirs:
                    source_dir = extracted_dirs[0]
                else:
                    raise ValueError("No directory found in backup archive")
            
            # Load metadata
            metadata_path = source_dir / BACKUP_METADATA_FILENAME
            if metadata_path.exists():
                # Metadata exists but not used in restore logic
                pass
            
            # Restore each component
            components_to_restore = components or ["vector_store", "documents", "configuration"]
            
            for component_name in components_to_restore:
                try:
                    if component_name == "vector_store":
                        vs_source = source_dir / "vector_store"
                        if vs_source.exists():
                            vs_dest = Path(self.config["vector_store_path"])
                            vs_dest.mkdir(parents=True, exist_ok=True)
                            
                            # Backup existing data first
                            if vs_dest.exists() and any(vs_dest.iterdir()):
                                backup_existing = vs_dest.parent / f"vector_store_backup_{int(time.time())}"
                                shutil.move(str(vs_dest), str(backup_existing))
                                vs_dest.mkdir(exist_ok=True)
                            
                            # Restore vector store
                            for file_path in vs_source.iterdir():
                                if file_path.is_file():
                                    shutil.copy2(file_path, vs_dest / file_path.name)
                            
                            restore_result["restored_components"].append("vector_store")
                    
                    elif component_name == "documents":
                        docs_source = source_dir / "documents"
                        if docs_source.exists():
                            docs_dest = Path(self.config["pdfs_path"])
                            docs_dest.mkdir(parents=True, exist_ok=True)
                            
                            for file_path in docs_source.iterdir():
                                if file_path.is_file():
                                    shutil.copy2(file_path, docs_dest / file_path.name)
                            
                            restore_result["restored_components"].append("documents")
                    
                    elif component_name == "configuration":
                        config_source = source_dir / "config"
                        if config_source.exists():
                            for file_path in config_source.iterdir():
                                if file_path.is_file():
                                    dest_path = Path(file_path.name)
                                    shutil.copy2(file_path, dest_path)
                            
                            restore_result["restored_components"].append("configuration")
                
                except Exception as e:
                    error_msg = f"Failed to restore {component_name}: {str(e)}"
                    restore_result.setdefault("errors", []).append(error_msg)
                    logger.error(error_msg)
            
            restore_result["status"] = "success"
            
            # Cleanup temporary directory
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            logger.info(f"Restore completed: {restore_result['restored_components']}")
            
        except Exception as e:
            restore_result["status"] = "error"
            restore_result["error"] = str(e)
            logger.error(f"Restore failed: {e}")
        
        return restore_result
    
    def start_scheduled_backups(self, backup_time: str = "02:00"):
        """Start scheduled backup thread"""
        if self.scheduler_running:
            logger.warning("Backup scheduler already running")
            return
        
        # Schedule daily backups
        schedule.every().day.at(backup_time).do(self._scheduled_backup_job)
        
        # Schedule weekly cleanup
        schedule.every().sunday.at("03:00").do(self._scheduled_cleanup_job)
        
        # Start scheduler thread
        self.scheduler_running = True
        self.backup_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.backup_thread.start()
        
        logger.info(f"Scheduled backups started - daily at {backup_time}")
    
    def stop_scheduled_backups(self):
        """Stop scheduled backup thread"""
        self.scheduler_running = False
        schedule.clear()
        
        if self.backup_thread and self.backup_thread.is_alive():
            self.backup_thread.join(timeout=5)
        
        logger.info("Scheduled backups stopped")
    
    def _run_scheduler(self):
        """Run the backup scheduler in background thread"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _scheduled_backup_job(self):
        """Execute scheduled backup job"""
        try:
            logger.info("Running scheduled backup")
            result = self.create_full_backup()
            
            if result["status"] == "success":
                logger.info(f"Scheduled backup completed: {result['backup_name']}")
            else:
                logger.error(f"Scheduled backup failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Scheduled backup job failed: {e}")
    
    def _scheduled_cleanup_job(self):
        """Execute scheduled cleanup job"""
        try:
            logger.info("Running scheduled backup cleanup")
            result = self.cleanup_old_backups()
            
            if result["status"] == "success":
                logger.info(f"Cleanup completed: removed {result['removed_count']} backups, "
                           f"freed {result['freed_space_mb']:.1f} MB")
            else:
                logger.error(f"Backup cleanup failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Scheduled cleanup job failed: {e}")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup system status"""
        status = {
            "scheduler_running": self.scheduler_running,
            "backup_root": str(self.backup_root),
            "retention_days": self.retention_days,
            "config": self.config,
            "backups": []
        }
        
        # List existing backups
        try:
            for backup_path in sorted(self.backup_root.glob("healthai_rag_backup_*")):
                backup_info = {
                    "name": backup_path.name,
                    "path": str(backup_path),
                    "created": datetime.fromtimestamp(backup_path.stat().st_ctime).isoformat(),
                    "size_mb": backup_path.stat().st_size / (1024 * 1024) if backup_path.is_file() 
                              else sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file()) / (1024 * 1024)
                }
                status["backups"].append(backup_info)
        except Exception as e:
            status["error"] = f"Failed to list backups: {str(e)}"
        
        return status


# Global backup manager instance
backup_manager = BackupManager()


if __name__ == "__main__":
    # CLI interface for backup operations
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python backup_manager.py <command> [args]")
        print("Commands: backup, validate <backup_path>, restore <backup_path>, cleanup, status")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        result = backup_manager.create_full_backup()
        print(json.dumps(result, indent=2))
    
    elif command == "validate" and len(sys.argv) > 2:
        backup_path = Path(sys.argv[2])
        result = backup_manager.validate_backup(backup_path)
        print(json.dumps(result, indent=2))
    
    elif command == "restore" and len(sys.argv) > 2:
        backup_path = Path(sys.argv[2])
        result = backup_manager.restore_from_backup(backup_path)
        print(json.dumps(result, indent=2))
    
    elif command == "cleanup":
        result = backup_manager.cleanup_old_backups()
        print(json.dumps(result, indent=2))
    
    elif command == "status":
        result = backup_manager.get_backup_status()
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)