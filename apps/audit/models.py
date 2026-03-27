"""Audit Logging Models"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import BaseModel


class AuditLog(BaseModel):
    """Immutable audit log for all system actions"""
    
    ACTION_CHOICES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('download', 'Download'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    
    # Request information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Changes (for update operations)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        app_label = 'audit'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['model_name', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action.upper()} - {self.model_name} - {self.object_id}"


class ActivityLog(BaseModel):
    """Activity log for PR lifecycle events"""
    
    EVENT_CHOICES = (
        ('pr_created', 'PR Created'),
        ('pr_submitted', 'PR Submitted'),
        ('pr_approved', 'PR Approved'),
        ('pr_rejected', 'PR Rejected'),
        ('pr_closed', 'PR Closed'),
        ('item_added', 'Item Added'),
        ('item_modified', 'Item Modified'),
        ('attachment_added', 'Attachment Added'),
        ('approval_requested', 'Approval Requested'),
        ('approval_completed', 'Approval Completed'),
        ('comment_added', 'Comment Added'),
    )
    
    pr = models.ForeignKey('pr.PurchaseRequisition', on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = 'audit'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['pr', 'created_at']),
            models.Index(fields=['user', 'event']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.pr.pr_number} - {self.event}"


class ApprovalHistory(BaseModel):
    """Complete approval trail for PRs"""
    
    STATUS_CHOICES = (
        ('assigned', 'Assigned'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
    )
    
    pr = models.ForeignKey('pr.PurchaseRequisition', on_delete=models.CASCADE, related_name='approval_history')
    approval_level = models.IntegerField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='given_approvals')
    approval_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    
    class Meta:
        app_label = 'audit'
        verbose_name = 'Approval History'
        verbose_name_plural = 'Approval History'
        indexes = [
            models.Index(fields=['pr', 'approval_level']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.pr.pr_number} - Level {self.approval_level} - {self.status}"
