"""
Dashboard views showing PR statistics, approvals, and activity tracking.
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum, Q, F, Case, When
from django.utils import timezone
from datetime import timedelta

from apps.pr.models import PurchaseRequisition, PRApproval, PRItem
from apps.audit.models import AuditLog, ActivityLog
from apps.attachments.models import Attachment


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard with PR statistics and overview."""
    
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Overall statistics
        context['total_prs'] = PurchaseRequisition.objects.count()
        context['pending_approval'] = PurchaseRequisition.objects.filter(
            status='PENDING_APPROVAL'
        ).count()
        context['approved'] = PurchaseRequisition.objects.filter(
            status='APPROVED'
        ).count()
        context['rejected'] = PurchaseRequisition.objects.filter(
            status='REJECTED'
        ).count()
        
        # Total value statistics
        total_value = PRItem.objects.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or 0
        context['total_pr_value'] = total_value
        
        # User-specific statistics
        if user.role.name == 'Requester':
            context['my_prs'] = PurchaseRequisition.objects.filter(
                created_by=user
            ).count()
            context['my_pending'] = PurchaseRequisition.objects.filter(
                created_by=user, status='PENDING_APPROVAL'
            ).count()
            context['my_approved'] = PurchaseRequisition.objects.filter(
                created_by=user, status='APPROVED'
            ).count()
        
        elif user.role.name == 'Approver':
            context['my_pending_approvals'] = PRApproval.objects.filter(
                approver=user, approval_status='PENDING'
            ).count()
            context['my_approved_prs'] = PRApproval.objects.filter(
                approver=user, approval_status='APPROVED'
            ).count()
            context['my_rejected_prs'] = PRApproval.objects.filter(
                approver=user, approval_status='REJECTED'
            ).count()
        
        # Recent PRs
        context['recent_prs'] = PurchaseRequisition.objects.order_by(
            '-created_at'
        )[:10]
        
        # PR status distribution
        status_dist = PurchaseRequisition.objects.values('status').annotate(
            count=Count('id')
        )
        context['status_distribution'] = list(status_dist)
        
        # Monthly PR trend
        today = timezone.now()
        last_12_months = [today - timedelta(days=30*i) for i in range(12)]
        
        monthly_trend = []
        for month_date in reversed(last_12_months):
            start_date = month_date.replace(day=1)
            if month_date.month == 12:
                end_date = month_date.replace(year=month_date.year + 1, month=1)
            else:
                end_date = month_date.replace(month=month_date.month + 1)
            
            count = PurchaseRequisition.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()
            
            monthly_trend.append({
                'month': start_date.strftime('%b %Y'),
                'count': count
            })
        
        context['monthly_trend'] = monthly_trend
        
        # Recent activities
        context['recent_activities'] = ActivityLog.objects.order_by(
            '-created_at'
        )[:15]
        
        # PR by type distribution
        pr_by_type = PurchaseRequisition.objects.values('pr_type').annotate(
            count=Count('id'), total_value=Sum(F('items__total_value'))
        )
        context['pr_by_type'] = list(pr_by_type)
        
        return context


class MyPRsDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard for requester showing their PRs."""
    
    template_name = 'dashboard/my_prs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all PRs created by user
        prs = PurchaseRequisition.objects.filter(created_by=user).order_by('-created_at')
        
        # Statistics
        context['total_prs'] = prs.count()
        context['draft_prs'] = prs.filter(status='DRAFT').count()
        context['pending_prs'] = prs.filter(status='PENDING_APPROVAL').count()
        context['approved_prs'] = prs.filter(status='APPROVED').count()
        context['rejected_prs'] = prs.filter(status='REJECTED').count()
        
        # Total value
        context['total_value'] = prs.aggregate(
            total=Sum(F('items__total_value'))
        )['total'] or 0
        
        # Recent PRs
        context['recent_prs'] = prs[:20]
        
        # Status distribution
        context['status_dist'] = prs.values('status').annotate(count=Count('id'))
        
        return context


class ApprovalsQueueView(LoginRequiredMixin, TemplateView):
    """Dashboard for approvers showing pending approvals."""
    
    template_name = 'dashboard/approvals_queue.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get pending approvals
        pending = PRApproval.objects.filter(
            approver=user, approval_status='PENDING'
        ).select_related('purchase_requisition').order_by('created_at')
        
        context['pending_approvals'] = pending
        context['pending_count'] = pending.count()
        
        # Statistics
        context['total_approved'] = PRApproval.objects.filter(
            approver=user, approval_status='APPROVED'
        ).count()
        
        context['total_rejected'] = PRApproval.objects.filter(
            approver=user, approval_status='REJECTED'
        ).count()
        
        # Oldest pending approval (for urgency)
        oldest = pending.first()
        if oldest:
            context['oldest_pending'] = oldest
            days_pending = (timezone.now() - oldest.created_at).days
            context['oldest_days'] = days_pending
        
        # Group by PR type
        context['pending_by_type'] = pending.values(
            'purchase_requisition__pr_type'
        ).annotate(count=Count('id'))
        
        return context


class AuditDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard for audit/admin showing system activity."""
    
    template_name = 'dashboard/audit_dashboard.html'
    
    def test_func(self):
        """Only admin can view."""
        return self.request.user.role.name == 'Admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recent audit logs
        context['recent_audits'] = AuditLog.objects.order_by(
            '-created_at'
        )[:50]
        
        # Activity by action type
        context['actions'] = AuditLog.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Activity by user
        context['users_activity'] = AuditLog.objects.values(
            'user__first_name', 'user__last_name'
        ).annotate(count=Count('id')).order_by('-count')[:10]
        
        # Last 7 days activity trend
        last_7_days = timezone.now() - timedelta(days=7)
        daily_activity = AuditLog.objects.filter(
            created_at__gte=last_7_days
        ).values('created_at__date').annotate(count=Count('id')).order_by('created_at__date')
        
        context['daily_activity'] = list(daily_activity)
        
        # File operations
        context['file_uploads'] = AuditLog.objects.filter(
            action='FILE_UPLOADED'
        ).count()
        context['file_downloads'] = AuditLog.objects.filter(
            action='FILE_DOWNLOADED'
        ).count()
        
        return context


class ReportsView(LoginRequiredMixin, TemplateView):
    """Reports and data export dashboard."""
    
    template_name = 'dashboard/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # PR aging report
        today = timezone.now()
        pending_prs = PurchaseRequisition.objects.filter(
            status='PENDING_APPROVAL'
        ).select_related('created_by')
        
        aging_data = []
        for pr in pending_prs:
            days_pending = (today - pr.submitted_date).days if pr.submitted_date else (today - pr.created_at).days
            aging_data.append({
                'pr_id': pr.pr_id,
                'requester': pr.created_by.get_full_name(),
                'days_pending': days_pending,
                'value': pr.items.aggregate(Sum('total_value'))['total_value__sum'] or 0
            })
        
        context['aging_report'] = sorted(aging_data, key=lambda x: x['days_pending'], reverse=True)
        
        # Approval authority efficiency
        approvers = PRApproval.objects.values('approver__first_name', 'approver__last_name').annotate(
            total=Count('id'),
            approved=Count(Case(When(approval_status='APPROVED', then=1))),
            rejected=Count(Case(When(approval_status='REJECTED', then=1))),
            pending=Count(Case(When(approval_status='PENDING', then=1)))
        )
        
        context['approver_stats'] = list(approvers)
        
        # Top uploaders by attachment count (proxy metric for vendor documentation volume)
        context['top_vendors'] = Attachment.objects.values(
            'uploaded_by__first_name', 'uploaded_by__last_name'
        ).annotate(count=Count('id')).order_by('-count')[:10]
        
        return context
