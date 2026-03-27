"""
Notification Services
COMMENTED - Uncomment when email credentials are available
"""

# from django.core.mail import send_mail
# from django.conf import settings
# from django.template.loader import render_to_string
# from apps.notifications.models import Notification, NotificationTemplate
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class EmailNotificationService:
#     """Service for sending email notifications"""
#
#     @staticmethod
#     def send_approval_request(pr, approver_email):
#         """Send approval request email"""
#         try:
#             subject = f"PR Approval Required - {pr.pr_number}"
#             message = f"""
#             Hello,
#
#             A new Purchase Requisition requires your approval.
#
#             PR Number: {pr.pr_number}
#             Amount: ₹{pr.grand_total:,.2f}
#             Requester: {pr.requester.get_full_name()}
#             Department: {pr.department}
#
#             Purpose: {pr.purpose_of_requirement}
#
#             Please login to the system to review and approve this PR.
#
#             Best regards,
#             PR Management System
#             """
#
#             # send_mail(
#             #     subject,
#             #     message,
#             #     settings.DEFAULT_FROM_EMAIL,
#             #     [approver_email],
#             #     fail_silently=False,
#             # )
#             logger.info(f"Email notification sent to {approver_email} for PR {pr.pr_number}")
#             return True
#         except Exception as e:
#             logger.error(f"Error sending email notification: {e}")
#             return False
#
#     @staticmethod
#     def send_approval_notification(pr, approver_email, status):
#         """Send PR approval status notification"""
#         try:
#             subject = f"PR {status.upper()} - {pr.pr_number}"
#             message = f"""
#             Hello,
#
#             Your Purchase Requisition has been {status}.
#
#             PR Number: {pr.pr_number}
#             Amount: ₹{pr.grand_total:,.2f}
#             Status: {status.upper()}
#
#             Thank you,
#             PR Management System
#             """
#
#             # send_mail(
#             #     subject,
#             #     message,
#             #     settings.DEFAULT_FROM_EMAIL,
#             #     [approver_email],
#             #     fail_silently=False,
#             # )
#             logger.info(f"Status notification sent to {approver_email} for PR {pr.pr_number}")
#             return True
#         except Exception as e:
#             logger.error(f"Error sending status notification: {e}")
#             return False
