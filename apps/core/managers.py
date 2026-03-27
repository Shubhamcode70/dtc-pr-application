"""
Custom managers for queryset optimization
"""

from django.db import models


class BaseQuerySet(models.QuerySet):
    """Base QuerySet with common filtering methods"""

    def active(self):
        """Return only active (non-deleted) records"""
        return self.filter(is_deleted=False)

    def deleted(self):
        """Return only deleted records"""
        return self.filter(is_deleted=True)

    def with_deleted(self):
        """Return all records including deleted ones"""
        return self.model.all_objects.filter(pk__in=self.values_list('pk', flat=True))


class BaseManager(models.Manager):
    """Base manager using BaseQuerySet"""

    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def deleted(self):
        return self.get_queryset().deleted()

    def with_deleted(self):
        return self.get_queryset().with_deleted()
