"""
Custom Storage Backend for PR Attachments
Swappable design - can be extended to S3, Azure, etc.
"""

import os
import hashlib
from pathlib import Path
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from apps.core.utils import generate_unique_filename


class PRFileStorage(FileSystemStorage):
    """
    Custom file storage for PR attachments
    Organizes files by date and PR ID
    """
    
    def __init__(self):
        super().__init__(
            location=os.path.join(settings.MEDIA_ROOT, 'pr_attachments'),
            base_url=f"{settings.MEDIA_URL}pr_attachments/"
        )
    
    def _full_path(self, name):
        """Get full path for file"""
        if name.startswith(self.location):
            return name
        return os.path.join(self.location, name)
    
    def save(self, name, content, max_length=None):
        """Save file with unique name and structured path"""
        # Generate unique filename
        unique_name = generate_unique_filename(name)
        
        # Save with super()
        saved_name = super().save(unique_name, content, max_length)
        
        return saved_name
    
    def url(self, name):
        """Get URL for file"""
        return f"{self.base_url}{os.path.basename(name)}"
    
    @staticmethod
    def get_file_hash(file_obj):
        """Get SHA256 hash of file"""
        hasher = hashlib.sha256()
        file_obj.seek(0)
        for chunk in file_obj.chunks():
            hasher.update(chunk)
        file_obj.seek(0)
        return hasher.hexdigest()
    
    @staticmethod
    def get_pr_storage_path(pr_id, file_type='general'):
        """
        Get storage path for PR attachment
        Structure: pr_attachments/YYYY/MM/PR_ID/file_type/
        """
        from datetime import datetime
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        return f"{year}/{month}/PR_{pr_id}/{file_type}"


class LocalFileBackend:
    """
    Abstract backend for local file storage
    Provides interface for swapping storage implementations
    """
    
    def __init__(self):
        self.storage = PRFileStorage()
    
    def save_file(self, file_obj, pr_id, file_type='general'):
        """Save file and return path and hash"""
        path = PRFileStorage.get_pr_storage_path(pr_id, file_type)
        file_hash = PRFileStorage.get_file_hash(file_obj)
        
        # Save file
        filename = f"{path}/{generate_unique_filename(file_obj.name)}"
        saved_path = self.storage.save(filename, file_obj)
        
        return {
            'path': saved_path,
            'hash': file_hash,
            'size': file_obj.size,
            'url': self.storage.url(saved_path)
        }
    
    def delete_file(self, file_path):
        """Delete file from storage"""
        try:
            self.storage.delete(file_path)
            return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_url(self, file_path):
        """Get URL for file"""
        return self.storage.url(file_path)
    
    def file_exists(self, file_path):
        """Check if file exists"""
        return self.storage.exists(file_path)


# Factory function for storage backend
def get_storage_backend():
    """
    Get current storage backend
    Can be extended to support multiple backends (S3, Azure, etc.)
    """
    backend_name = getattr(settings, 'FILE_STORAGE_BACKEND', 'local')
    
    if backend_name == 'local':
        return LocalFileBackend()
    elif backend_name == 's3':
        # Future: S3FileBackend()
        raise NotImplementedError("S3 backend coming soon")
    else:
        return LocalFileBackend()
