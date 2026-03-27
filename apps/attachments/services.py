"""Attachment service utilities."""

import mimetypes
from django.utils import timezone


class AttachmentService:
    """Service class for validating and extracting metadata from uploaded files."""

    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'txt', 'csv', 'jpg', 'jpeg', 'png', 'gif'
    }
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def validate_file(self, file):
        if not file:
            return False, "No file provided"
        if file.size > self.MAX_FILE_SIZE:
            return False, f"File size exceeds {self.MAX_FILE_SIZE / 1024 / 1024}MB limit"
        ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"File type .{ext} not allowed"
        return True, None

    def get_file_metadata(self, file) -> dict:
        return {
            'name': file.name,
            'size': file.size,
            'mime_type': mimetypes.guess_type(file.name)[0],
            'uploaded_at': timezone.now(),
        }
