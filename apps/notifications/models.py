"""
Notification Models
Code is implemented but commented - add credentials to enable
"""

from django.db import models
from django.contrib.auth.models import User
from apps.core.models import AuditableModel


class NotificationTemplate(AuditableModel):
    """Notification templates for different events"""
    
    EVENT_TYPES = (
        ('pr_submitted', 'PR Submitted'),
        ('pr_approved', 'PR Approved'),
        ('pr_rejected', 'PR Rejected'),
        ('approval_requested', 'Approval Requested'),
        ('approval_completed', 'Approval Completed'),
    )
    
    event_type = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=200)
    email_subject = models.CharField(max_length=255)
    email_body = models.TextField(
        help_text="Use {pr_number}, {requester}, {amount} etc. for template variables"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'notifications'
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
    
    def __str__(self):
        return self.display_name


class Notification(AuditableModel):
    """User notifications"""
    
    TYPE_CHOICES = (
        ('email', 'Email'),
        ('in_app', 'In-App'),
        ('both', 'Both'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='both')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    related_pr = models.ForeignKey(
        'pr.PurchaseRequisition',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_date = models.DateTimeField(null=True, blank=True)
    read_date = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        app_label = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.user.username}"


class UserNotificationPreference(AuditableModel):
    """User preferences for notifications"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    
    # Email preferences
    email_on_pr_submitted = models.BooleanField(default=True)
    email_on_pr_approved = models.BooleanField(default=True)
    email_on_pr_rejected = models.BooleanField(default=True)
    email_on_approval_requested = models.BooleanField(default=True)
    email_digest = models.BooleanField(default=False)
    digest_frequency = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly')],
        default='daily'
    )
    
    # In-app notifications
    inapp_notifications = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'notifications'
        verbose_name = 'User Notification Preference'
        verbose_name_plural = 'User Notification Preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
