"""
Business Logic Services for PR Management
Separates complex business logic from views
"""

from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from apps.pr.models import (
    PurchaseRequisition, PRApproval, PRStatus, ApprovalChain, PRType
)
from apps.audit.models import ActivityLog
from apps.users.models import UserProfile
import logging

logger = logging.getLogger(__name__)


class PRService:
    """Service class for PR operations"""
    
    @staticmethod
    def generate_pr_number(pr_type):
        """Generate unique PR number with format: PR/MM/YYYY/XXX"""
        from datetime import datetime
        month = datetime.now().strftime('%m')
        year = datetime.now().strftime('%Y')
        
        # Count existing PRs this month
        count = PurchaseRequisition.objects.filter(
            created_at__month=datetime.now().month,
            created_at__year=datetime.now().year
        ).count() + 1
        
        return f"PR/{month}/{year}/{count:03d}"
    
    @staticmethod
    def create_pr(requester, pr_type, department, purpose, **kwargs):
        """Create a new PR"""
        try:
            pr = PurchaseRequisition.objects.create(
                pr_number=PRService.generate_pr_number(pr_type),
                requester=requester,
                pr_type=pr_type,
                department=department,
                purpose_of_requirement=purpose,
                status='draft',
                created_by=requester,
                **kwargs
            )
            
            logger.info(f"PR {pr.pr_number} created by {requester.username}")
            return pr
        except Exception as e:
            logger.error(f"Error creating PR: {e}")
            raise
    
    @staticmethod
    @transaction.atomic
    def submit_pr(pr, user):
        """Submit PR for approval"""
        if not pr.can_submit():
            raise ValueError("PR cannot be submitted in current state")
        
        # Calculate grand total
        total = sum(item.total_value or 0 for item in pr.pritem_set.all())
        pr.grand_total = total
        pr.status = 'submitted'
        pr.submitted_date = timezone.now()
        pr.updated_by = user
        pr.save()
        
        # Get applicable approval chains
        pr_type = pr.pr_type
        applicable_chains = ApprovalChain.get_applicable_chains(total, pr_type)
        
        if not applicable_chains:
            # No approval chain found, mark as no approval needed
            pr.status = 'approved'
            pr.approval_completed_date = timezone.now()
            pr.save()
            PRService.create_activity_log(pr, 'pr_approved', user, "Auto-approved (no approval chain)")
            logger.info(f"PR {pr.pr_number} auto-approved (no approval chain)")
            return pr
        
        # Use highest priority chain
        approval_chain = applicable_chains[0]
        pr.approval_chain = approval_chain
        pr.status = 'pending_approval'
        pr.save()
        
        # Create approval records
        PRService.create_approval_records(pr, approval_chain, user)
        
        # Log activity
        PRService.create_activity_log(
            pr, 'pr_submitted', user,
            f"PR submitted for approval via chain: {approval_chain.name}"
        )
        
        logger.info(f"PR {pr.pr_number} submitted for approval")
        return pr
    
    @staticmethod
    def create_approval_records(pr, approval_chain, submitted_by):
        """Create approval records based on approval chain"""
        approval_sequence = approval_chain.approval_sequence
        
        for level_config in approval_sequence:
            level = level_config.get('level', 1)
            role_name = level_config.get('role', 'approver')
            
            # Get users with this role
            role = UserProfile.objects.filter(
                role__name=role_name,
                is_approver=True,
                approval_limit__gte=pr.grand_total,
                is_active=True
            ).select_related('user')
            
            # Create approval record for first matching user
            if role.exists():
                first_approver = role.first().user
                PRApproval.objects.create(
                    pr=pr,
                    approval_level=level,
                    assigned_to=first_approver,
                    status='pending',
                    created_by=submitted_by
                )
                
                logger.info(f"Approval record created for {first_approver.username} at level {level}")
    
    @staticmethod
    @transaction.atomic
    def approve_pr(approval, user, comments=''):
        """Approve a PR"""
        if approval.status != 'pending':
            raise ValueError("This approval is not pending")
        
        approval.approved_by = user
        approval.approval_date = timezone.now()
        approval.comments = comments
        approval.status = 'approved'
        approval.save()
        
        pr = approval.pr
        
        # Check if all approvals at this level are completed
        pending_at_level = PRApproval.objects.filter(
            pr=pr,
            approval_level=approval.approval_level,
            status='pending'
        ).count()
        
        if pending_at_level == 0:
            # Check if there are more approval levels
            next_level = approval.approval_level + 1
            next_approvals = PRApproval.objects.filter(
                pr=pr,
                approval_level=next_level
            ).exists()
            
            if next_approvals:
                # More levels to approve
                pass
            else:
                # All approvals complete
                pr.status = 'approved'
                pr.approval_completed_date = timezone.now()
                pr.save()
                
                PRService.create_activity_log(
                    pr, 'pr_approved', user, "All approvals completed"
                )
                logger.info(f"PR {pr.pr_number} fully approved")
        
        PRService.create_activity_log(
            pr, 'approval_completed', user,
            f"Approved at level {approval.approval_level}"
        )
        
        return approval
    
    @staticmethod
    @transaction.atomic
    def reject_pr(approval, user, reason=''):
        """Reject a PR"""
        if approval.status != 'pending':
            raise ValueError("This approval is not pending")
        
        approval.approved_by = user
        approval.approval_date = timezone.now()
        approval.comments = reason
        approval.status = 'rejected'
        approval.save()
        
        pr = approval.pr
        pr.status = 'rejected'
        pr.approval_completed_date = timezone.now()
        pr.updated_by = user
        pr.save()
        
        # Clear other pending approvals
        PRApproval.objects.filter(
            pr=pr,
            status='pending'
        ).update(status='escalated')
        
        PRService.create_activity_log(
            pr, 'pr_rejected', user, f"Rejected at level {approval.approval_level}: {reason}"
        )
        
        logger.info(f"PR {pr.pr_number} rejected by {user.username}")
        return approval
    
    @staticmethod
    def create_activity_log(pr, event, user, description):
        """Create activity log entry"""
        ActivityLog.objects.create(
            pr=pr,
            user=user,
            event=event,
            description=description
        )
    
    @staticmethod
    def record_status_change(pr, to_status, user, reason=''):
        """Record PR status change"""
        PRStatus.objects.create(
            pr=pr,
            from_status=pr.status,
            to_status=to_status,
            changed_by=user,
            reason=reason
        )


class ApprovalChainService:
    """Service for approval chain operations"""
    
    @staticmethod
    def create_approval_chain(name, min_amount, max_amount, approval_sequence, **kwargs):
        """Create a new approval chain"""
        chain = ApprovalChain.objects.create(
            name=name,
            min_amount=min_amount,
            max_amount=max_amount,
            condition_type='amount_range',
            approval_sequence=approval_sequence,
            **kwargs
        )
        logger.info(f"Approval chain '{name}' created")
        return chain
    
    @staticmethod
    def get_applicable_chain(amount, pr_type=None):
        """Get the applicable approval chain for amount"""
        chains = ApprovalChain.get_applicable_chains(amount, pr_type)
        return chains[0] if chains else None


class PRApprovalService:
    """Backward-compatible wrapper used by legacy views."""

    def create_approval_chain(self, pr, total_value):
        chain = ApprovalChainService.get_applicable_chain(total_value, pr.pr_type)
        if chain:
            pr.approval_chain = chain
            pr.save(update_fields=['approval_chain', 'updated_at'])
        return chain

    def update_pr_status(self, pr):
        """Infer PR status from approval rows."""
        statuses = list(pr.approvals.values_list('status', flat=True))
        if any(s == 'rejected' for s in statuses):
            return 'rejected'
        if statuses and all(s == 'approved' for s in statuses):
            return 'approved'
        return 'pending_approval'


class PRGenerationService:
    """Legacy shim for PR number generation."""

    @staticmethod
    def generate(pr_type):
        return PRService.generate_pr_number(pr_type)
