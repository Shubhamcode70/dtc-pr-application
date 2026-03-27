"""
Base models for DTC PR Application
All models should inherit from BaseModel for consistent audit fields
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model providing common fields for all models.
    Ensures consistent audit tracking across the application.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='%(class)s_updated',
        null=True,
        blank=True
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='%(class)s_deleted',
        null=True,
        blank=True
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self, user=None):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self, user=None):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.updated_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_by'])


class SoftDeleteManager(models.Manager):
    """
    Custom manager for soft-deleted records.
    By default, excludes deleted records.
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """Return all records including deleted ones"""
        return super().get_queryset()

    def only_deleted(self):
        """Return only deleted records"""
        return super().get_queryset().filter(is_deleted=True)


class AuditableModel(BaseModel):
    """
    Model that provides soft delete functionality through SoftDeleteManager
    """
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # To access all records including deleted

    class Meta:
        abstract = True
