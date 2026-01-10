"""
Version Control & Snapshot System
Like Replit's snapshot engine - instant rollback capability
"""
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import hashlib

logger = logging.getLogger(__name__)


class VersionControlService:
    """Manage project versions and snapshots"""
    
    def __init__(self, db):
        self.db = db
        self.snapshots_collection = db.project_snapshots
    
    async def create_snapshot(
        self,
        project_id: str,
        user_id: str,
        files: List[Dict],
        message: Optional[str] = None,
        auto: bool = False
    ) -> Dict:
        """
        Create a snapshot of current project state
        
        Args:
            project_id: Project identifier
            user_id: User who created snapshot
            files: Current project files
            message: Optional snapshot message
            auto: Whether this is an automatic snapshot
            
        Returns:
            Snapshot information
        """
        try:
            # Generate snapshot ID from file content hash
            content_hash = self._generate_content_hash(files)
            
            # Check if identical snapshot exists
            existing = await self.snapshots_collection.find_one({
                "project_id": project_id,
                "content_hash": content_hash
            })
            
            if existing:
                logger.info(f"Identical snapshot already exists: {existing['snapshot_id']}")
                return {
                    "success": True,
                    "snapshot_id": existing["snapshot_id"],
                    "message": "Snapshot already exists (no changes)",
                    "is_new": False
                }
            
            # Create new snapshot
            now = datetime.now(timezone.utc)
            snapshot_id = f"snap_{now.strftime('%Y%m%d_%H%M%S')}_{content_hash[:8]}"
            
            snapshot_doc = {
                "snapshot_id": snapshot_id,
                "project_id": project_id,
                "user_id": user_id,
                "files": files,
                "content_hash": content_hash,
                "message": message or ("Auto-save" if auto else "Manual snapshot"),
                "auto_created": auto,
                "created_at": now.isoformat(),
                "file_count": len(files),
                "total_size": sum(len(f.get("content", "")) for f in files)
            }
            
            await self.snapshots_collection.insert_one(snapshot_doc)
            
            logger.info(f"Created snapshot: {snapshot_id} for project {project_id}")
            
            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "message": "Snapshot created successfully",
                "is_new": True,
                "created_at": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_snapshots(
        self,
        project_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get all snapshots for a project"""
        try:
            snapshots = await self.snapshots_collection.find(
                {"project_id": project_id},
                {"files": 0}  # Exclude file content for listing
            ).sort("created_at", -1).limit(limit).to_list(length=limit)
            
            return [
                {
                    "snapshot_id": s["snapshot_id"],
                    "message": s.get("message", ""),
                    "created_at": s.get("created_at"),
                    "file_count": s.get("file_count", 0),
                    "total_size": s.get("total_size", 0),
                    "auto_created": s.get("auto_created", False)
                }
                for s in snapshots
            ]
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []
    
    async def restore_snapshot(
        self,
        project_id: str,
        snapshot_id: str,
        user_id: str
    ) -> Dict:
        """
        Restore project to a specific snapshot
        Creates a new snapshot before restoring (safety)
        """
        try:
            # Get current project state
            current_project = await self.db.projects.find_one(
                {"project_id": project_id, "user_id": user_id}
            )
            
            if not current_project:
                return {
                    "success": False,
                    "error": "Project not found"
                }
            
            # Create safety snapshot of current state
            await self.create_snapshot(
                project_id,
                user_id,
                current_project.get("files", []),
                message="Auto-save before restore",
                auto=True
            )
            
            # Get target snapshot
            snapshot = await self.snapshots_collection.find_one({
                "snapshot_id": snapshot_id,
                "project_id": project_id
            })
            
            if not snapshot:
                return {
                    "success": False,
                    "error": "Snapshot not found"
                }
            
            # Restore files
            now = datetime.now(timezone.utc)
            await self.db.projects.update_one(
                {"project_id": project_id, "user_id": user_id},
                {
                    "$set": {
                        "files": snapshot["files"],
                        "updated_at": now.isoformat(),
                        "last_restored_from": snapshot_id
                    }
                }
            )
            
            logger.info(f"Restored project {project_id} to snapshot {snapshot_id}")
            
            return {
                "success": True,
                "message": "Project restored successfully",
                "snapshot_id": snapshot_id,
                "file_count": len(snapshot["files"])
            }
            
        except Exception as e:
            logger.error(f"Failed to restore snapshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def compare_snapshots(
        self,
        snapshot_id_1: str,
        snapshot_id_2: str
    ) -> Dict:
        """Compare two snapshots and return differences"""
        try:
            snapshot1 = await self.snapshots_collection.find_one({"snapshot_id": snapshot_id_1})
            snapshot2 = await self.snapshots_collection.find_one({"snapshot_id": snapshot_id_2})
            
            if not snapshot1 or not snapshot2:
                return {
                    "success": False,
                    "error": "One or both snapshots not found"
                }
            
            files1 = {f["path"]: f["content"] for f in snapshot1["files"]}
            files2 = {f["path"]: f["content"] for f in snapshot2["files"]}
            
            # Find changes
            added = [path for path in files2 if path not in files1]
            removed = [path for path in files1 if path not in files2]
            modified = [
                path for path in files1
                if path in files2 and files1[path] != files2[path]
            ]
            
            return {
                "success": True,
                "added_files": added,
                "removed_files": removed,
                "modified_files": modified,
                "total_changes": len(added) + len(removed) + len(modified)
            }
            
        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def auto_snapshot_on_change(
        self,
        project_id: str,
        user_id: str,
        files: List[Dict]
    ):
        """
        Automatically create snapshot on significant changes
        Called after file edits
        """
        # Only create auto-snapshot if files have changed significantly
        try:
            latest_snapshot = await self.snapshots_collection.find_one(
                {"project_id": project_id},
                sort=[("created_at", -1)]
            )
            
            if latest_snapshot:
                # Check if content has changed
                new_hash = self._generate_content_hash(files)
                if new_hash == latest_snapshot.get("content_hash"):
                    # No changes, skip snapshot
                    return
            
            # Create auto-snapshot
            await self.create_snapshot(
                project_id,
                user_id,
                files,
                message="Auto-save on edit",
                auto=True
            )
            
        except Exception as e:
            logger.error(f"Auto-snapshot failed: {e}")
    
    def _generate_content_hash(self, files: List[Dict]) -> str:
        """Generate hash of file contents for comparison"""
        # Sort files by path for consistent hashing
        sorted_files = sorted(files, key=lambda f: f.get("path", ""))
        
        # Concatenate all file contents
        content = "".join(
            f"{f.get('path', '')}:{f.get('content', '')}"
            for f in sorted_files
        )
        
        # Generate SHA256 hash
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def delete_old_snapshots(
        self,
        project_id: str,
        keep_count: int = 50
    ):
        """
        Clean up old snapshots, keeping only recent ones
        Keep manual snapshots, delete auto-snapshots
        """
        try:
            # Get all snapshots
            all_snapshots = await self.snapshots_collection.find(
                {"project_id": project_id}
            ).sort("created_at", -1).to_list(length=None)
            
            # Keep all manual snapshots + latest auto-snapshots
            manual = [s for s in all_snapshots if not s.get("auto_created")]
            auto = [s for s in all_snapshots if s.get("auto_created")]
            
            # Delete old auto-snapshots
            if len(auto) > keep_count:
                to_delete = auto[keep_count:]
                delete_ids = [s["snapshot_id"] for s in to_delete]
                
                result = await self.snapshots_collection.delete_many({
                    "snapshot_id": {"$in": delete_ids}
                })
                
                logger.info(f"Deleted {result.deleted_count} old snapshots for project {project_id}")
                
        except Exception as e:
            logger.error(f"Failed to clean up snapshots: {e}")
