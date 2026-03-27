"""Attachment and File Management Models"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import AuditableModel


class AttachmentType(models.Model):
    """Types of attachments"""
    
    TYPE_CHOICES = (
        ('quotation', 'Quotation'),
        ('comparison_sheet', 'Comparison Sheet'),
        ('rfq', 'Request for Quotation'),
        ('invoice', 'Invoice'),
        ('delivery_note', 'Delivery Note'),
        ('purchase_order', 'Purchase Order'),
        ('other', 'Other Document'),
    )
    
    type_key = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=False)
    allowed_extensions = models.CharField(
        max_length=255,
        default='pdf,doc,docx,xls,xlsx',
        help_text="Comma-separated list of allowed file extensions"
    )
    
    class Meta:
        app_label = 'attachments'
        verbose_name = 'Attachment Type'
        verbose_name_plural = 'Attachment Types'
    
    def __str__(self):
        return self.display_name


class Attachment(AuditableModel):
    """File attachments to PRs"""
    
    pr = models.ForeignKey('pr.PurchaseRequisition', on_delete=models.CASCADE, related_name='attachments')
    attachment_type = models.ForeignKey(AttachmentType, on_delete=models.PROTECT)
    
    file = models.FileField(upload_to='pr_attachments/')
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # in bytes
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)  # SHA256
    mime_type = models.CharField(max_length=100)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    
    # Scanning and validation
    is_scanned = models.BooleanField(default=False)
    scan_result = models.CharField(max_length=20, blank=True)  # clean, infected, error
    scan_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'attachments'
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'
        indexes = [
            models.Index(fields=['pr', 'attachment_type']),
            models.Index(fields=['file_hash']),
            models.Index(fields=['uploaded_by', 'upload_date']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.attachment_type.display_name})"


class FileIndex(AuditableModel):
    """Index for quick file lookups"""
    
    attachment = models.OneToOneField(Attachment, on_delete=models.CASCADE, related_name='index')
    file_path = models.CharField(max_length=500, unique=True, db_index=True)
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'attachments'
        verbose_name = 'File Index'
        verbose_name_plural = 'File Indexes'
    
    def __str__(self):
        return f"Index: {self.file_path}"


class AccessLog(AuditableModel):
    """Log file access for audit trail"""
    
    ACTION_CHOICES = (
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('view', 'View'),
        ('delete', 'Delete'),
    )
    
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'attachments'
        verbose_name = 'File Access Log'
        verbose_name_plural = 'File Access Logs'
        indexes = [
            models.Index(fields=['attachment', 'created_at']),
            models.Index(fields=['user', 'action']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.attachment.original_filename}"
