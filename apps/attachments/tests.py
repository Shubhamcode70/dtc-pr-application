"""
Tests for file attachment and storage management.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from apps.attachments.models import Attachment, FileIndex
from apps.attachments.storage import LocalFileStorage
from apps.pr.models import PurchaseRequisition
from apps.users.models import Role
import os

User = get_user_model()


class AttachmentStorageTestCase(TestCase):
    """Test file storage functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.storage = LocalFileStorage()
        
        # Create role
        self.role = Role.objects.create(name='Test Role')
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.role = self.role
        self.user.save()
        
        # Create PR
        self.pr = PurchaseRequisition.objects.create(
            created_by=self.user,
            requester_name='Test User',
            department='IT',
            purpose_of_requirement='Test requirement',
            pr_type='OPEX',
            status='DRAFT'
        )
    
    def test_file_storage_path_organization(self):
        """Test that files are organized by year/month/pr_id."""
        file_name = 'test_document.pdf'
        pr = self.pr
        
        # Get organized path
        now = timezone.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        expected_path = f'pr_attachments/{year}/{month}/{pr.pr_id}/{file_name}'
        
        # Verify path structure
        self.assertIn(year, expected_path)
        self.assertIn(month, expected_path)
        self.assertIn(str(pr.pr_id), expected_path)
    
    def test_attachment_soft_delete(self):
        """Test soft delete functionality."""
        file = SimpleUploadedFile("test.txt", b"test content")
        
        attachment = Attachment.objects.create(
            purchase_requisition=self.pr,
            uploaded_by=self.user,
            file=file,
            attachment_type='OTHER'
        )
        
        # Soft delete
        attachment.is_deleted = True
        attachment.save()
        
        # Verify it's marked as deleted but still in DB
        attachment.refresh_from_db()
        self.assertTrue(attachment.is_deleted)
        self.assertTrue(Attachment.objects.filter(id=attachment.id).exists())
    
    def test_file_index_creation(self):
        """Test file index metadata storage."""
        file = SimpleUploadedFile("test.pdf", b"PDF content here")
        
        attachment = Attachment.objects.create(
            purchase_requisition=self.pr,
            uploaded_by=self.user,
            file=file,
            attachment_type='OTHER'
        )
        
        index = FileIndex.objects.create(
            attachment=attachment,
            file_path=str(attachment.file),
            file_size=file.size,
            mime_type='application/pdf'
        )
        
        self.assertEqual(index.file_size, len(b"PDF content here"))
        self.assertEqual(index.mime_type, 'application/pdf')
