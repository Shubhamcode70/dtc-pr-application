"""
User and Role Management Models
"""

from django.db import models
from django.contrib.auth.models import User, Group, Permission
from apps.core.models import BaseModel


class Role(BaseModel):
    """
    Role definitions for RBAC
    Predefined roles: Admin, Manager, Requester, Approver, Finance
    """
    
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('requester', 'Requester'),
        ('approver', 'Approver'),
        ('finance', 'Finance Officer'),
    )
    
    name = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        unique=True,
        db_index=True
    )
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'users'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.get_name_display()}"


class UserProfile(BaseModel):
    """Extended user profile with additional information"""
    
    DEPARTMENT_CHOICES = (
        ('dtc', 'DTC (Direct to Consumer)'),
        ('operations', 'Operations'),
        ('finance', 'Finance'),
        ('procurement', 'Procurement'),
        ('it', 'IT'),
        ('hr', 'Human Resources'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )
    is_approver = models.BooleanField(default=False, db_index=True)
    approval_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Maximum amount this user can approve"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'users'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_approver', 'approval_limit']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role.get_name_display() if self.role else 'No Role'})"
    
    @property
    def has_approval_authority(self):
        """Check if user has any approval authority"""
        return self.is_approver and self.approval_limit > 0
    
    def can_approve_amount(self, amount):
        """Check if user can approve a specific amount"""
        if not self.is_approver:
            return False
        return self.approval_limit >= amount


class PermissionGroup(BaseModel):
    """Custom permission grouping for better RBAC management"""
    
    PERMISSION_CATEGORIES = (
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('approve', 'Approve'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('admin', 'Admin'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=PERMISSION_CATEGORIES)
    description = models.TextField(blank=True)
    roles = models.ManyToManyField(Role, related_name='permission_groups')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'users'
        verbose_name = 'Permission Group'
        verbose_name_plural = 'Permission Groups'
        unique_together = ['name', 'category']
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class LoginAttempt(BaseModel):
    """Track user login attempts for security"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_attempts')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, blank=True)
    
    class Meta:
        app_label = 'users'
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.user.username} - {status} ({self.created_at})"
