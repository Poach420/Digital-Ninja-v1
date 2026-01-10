"""
File Storage Service
Handle file uploads, images, documents
Like Base44's automatic storage system
"""
import os
import uuid
import logging
from typing import Dict, Optional, BinaryIO, List
from datetime import datetime, timezone
import mimetypes
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)


class FileStorageService:
    """Manage file uploads and storage"""
    
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.storage_path / "images").mkdir(exist_ok=True)
        (self.storage_path / "documents").mkdir(exist_ok=True)
        (self.storage_path / "media").mkdir(exist_ok=True)
        (self.storage_path / "temp").mkdir(exist_ok=True)
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        project_id: Optional[str] = None
    ) -> Dict:
        """
        Upload a file to storage
        
        Args:
            file_content: File bytes
            filename: Original filename
            user_id: User who uploaded
            project_id: Optional project association
            
        Returns:
            Upload result with file URL
        """
        try:
            # Generate unique file ID
            file_id = f"{uuid.uuid4().hex[:12]}"
            file_ext = Path(filename).suffix
            
            # Determine storage category
            mime_type, _ = mimetypes.guess_type(filename)
            category = self._categorize_file(mime_type)
            
            # Generate storage path
            stored_filename = f"{file_id}{file_ext}"
            storage_subpath = self.storage_path / category / stored_filename
            
            # Save file
            async with aiofiles.open(storage_subpath, 'wb') as f:
                await f.write(file_content)
            
            # Generate public URL
            public_url = f"/storage/{category}/{stored_filename}"
            
            now = datetime.now(timezone.utc)
            
            file_info = {
                "file_id": file_id,
                "filename": filename,
                "stored_filename": stored_filename,
                "url": public_url,
                "category": category,
                "mime_type": mime_type or "application/octet-stream",
                "size": len(file_content),
                "user_id": user_id,
                "project_id": project_id,
                "uploaded_at": now.isoformat()
            }
            
            logger.info(f"Uploaded file: {filename} ({len(file_content)} bytes)")
            
            return {
                "success": True,
                **file_info
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_file(self, file_id: str) -> Optional[Dict]:
        """Retrieve file information"""
        # Search in all categories
        for category in ["images", "documents", "media"]:
            category_path = self.storage_path / category
            for file_path in category_path.glob(f"{file_id}*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    return {
                        "file_id": file_id,
                        "path": str(file_path),
                        "url": f"/storage/{category}/{file_path.name}",
                        "size": stat.st_size,
                        "category": category
                    }
        return None
    
    async def delete_file(self, file_id: str) -> Dict:
        """Delete a file from storage"""
        try:
            file_info = await self.get_file(file_id)
            
            if not file_info:
                return {
                    "success": False,
                    "error": "File not found"
                }
            
            # Delete physical file
            file_path = Path(file_info["path"])
            file_path.unlink(missing_ok=True)
            
            logger.info(f"Deleted file: {file_id}")
            
            return {
                "success": True,
                "message": "File deleted"
            }
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_project_files(
        self,
        project_id: str,
        db
    ) -> List[Dict]:
        """List all files associated with a project"""
        try:
            files = await db.project_files.find({
                "project_id": project_id
            }).sort("uploaded_at", -1).to_list(length=100)
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list project files: {e}")
            return []
    
    def _categorize_file(self, mime_type: Optional[str]) -> str:
        """Categorize file based on MIME type"""
        if not mime_type:
            return "documents"
        
        if mime_type.startswith("image/"):
            return "images"
        elif mime_type.startswith("video/") or mime_type.startswith("audio/"):
            return "media"
        else:
            return "documents"
    
    async def generate_presigned_url(
        self,
        file_id: str,
        expiry_seconds: int = 3600
    ) -> Optional[str]:
        """
        Generate a temporary presigned URL for file access
        (For production, would use S3/CDN)
        """
        file_info = await self.get_file(file_id)
        if not file_info:
            return None
        
        # In production, this would generate S3 presigned URL
        # For now, return direct URL with expiry token
        token = uuid.uuid4().hex[:16]
        return f"{file_info['url']}?token={token}&expires={expiry_seconds}"
    
    async def optimize_image(
        self,
        file_path: Path,
        max_width: int = 1920,
        quality: int = 85
    ) -> Dict:
        """
        Optimize uploaded images
        Resize and compress for web delivery
        """
        try:
            from PIL import Image
            
            img = Image.open(file_path)
            
            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Save optimized
            img.save(file_path, 'JPEG', quality=quality, optimize=True)
            
            return {
                "success": True,
                "message": "Image optimized"
            }
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_temp_files(self, age_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            temp_path = self.storage_path / "temp"
            now = datetime.now().timestamp()
            age_seconds = age_hours * 3600
            
            deleted = 0
            for file_path in temp_path.glob("*"):
                if file_path.is_file():
                    file_age = now - file_path.stat().st_mtime
                    if file_age > age_seconds:
                        file_path.unlink()
                        deleted += 1
            
            logger.info(f"Cleaned up {deleted} temporary files")
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
