"""
Celery Tasks for Notifications
COMMENTED - Uncomment when redis/celery and email credentials are configured
"""

# from celery import shared_task
# from django.conf import settings
# from apps.notifications.models import Notification
# from apps.notifications.services import EmailNotificationService
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# @shared_task
# def send_notification_email(notification_id):
#     """
#     Celery task to send notification email asynchronously
#     """
#     try:
#         notification = Notification.objects.get(pk=notification_id)
#         
#         # Send email
#         if notification.notification_type in ['email', 'both']:
#             EmailNotificationService.send_approval_request(
#                 notification.related_pr,
#                 notification.user.email
#             )
#         
#         notification.status = 'sent'
#         notification.save()
#         
#         logger.info(f"Notification {notification_id} sent successfully")
#         return True
#     except Exception as e:
#         logger.error(f"Error sending notification {notification_id}: {e}")
#         return False
#
#
# @shared_task
# def send_approval_request(pr_id, approver_id):
#     """Send approval request to approver"""
#     try:
#         from apps.pr.models import PurchaseRequisition
#         from django.contrib.auth.models import User
#         
#         pr = PurchaseRequisition.objects.get(pk=pr_id)
#         approver = User.objects.get(pk=approver_id)
#         
#         EmailNotificationService.send_approval_request(pr, approver.email)
#         
#         logger.info(f"Approval request sent to {approver.username} for PR {pr.pr_number}")
#         return True
#     except Exception as e:
#         logger.error(f"Error sending approval request: {e}")
#         return False
#
#
# @shared_task
# def send_digest_emails():
#     """Send daily/weekly digest emails to users"""
#     logger.info("Starting digest email task")
#     # Implementation coming soon
#     return True
