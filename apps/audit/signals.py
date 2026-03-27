"""
Signals for automatic audit logging on model changes
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.audit.models import ActivityLog


@receiver(post_save, sender='pr.PurchaseRequisition')
def log_pr_changes(sender, instance, created, **kwargs):
    """Log PR creation and updates"""
    event = 'pr_created' if created else 'pr_updated'
    ActivityLog.objects.create(
        pr=instance,
        user=instance.created_by if created else instance.updated_by,
        event=event,
        description=f"PR {instance.pr_number} {'created' if created else 'updated'}",
    )
