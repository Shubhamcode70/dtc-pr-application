"""
Purchase Requisition Models
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, DecimalValidator
from apps.core.models import AuditableModel
from apps.users.models import UserProfile, Role
import uuid


class PRType(models.Model):
    """PR Type definitions: CAPEX, OPEX, etc."""
    
    TYPE_CHOICES = (
        ('capex', 'Capital Expenditure'),
        ('opex', 'Operating Expenditure'),
        ('maintenance', 'Maintenance'),
        ('service', 'Service'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'pr'
        verbose_name = 'PR Type'
        verbose_name_plural = 'PR Types'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ApprovalChain(AuditableModel):
    """
    CRITICAL: Rule-based approval chain configuration
    Defines who can approve PRs based on amount thresholds and other criteria
    """
    
    CONDITION_TYPES = (
        ('amount_range', 'Amount Range'),
        ('pr_type', 'PR Type'),
        ('department', 'Department'),
        ('combined', 'Combined'),
    )
    
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES)
    
    # Amount range conditions
    min_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    max_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # PR Type condition
    pr_types = models.ManyToManyField(PRType, blank=True)
    
    # Approval sequence
    approval_sequence = models.JSONField(
        default=list,
        help_text="List of approval levels with roles and number of approvers"
    )
    # Example: [
    #   {"level": 1, "role": "manager", "min_approvers": 1, "parallel": false},
    #   {"level": 2, "role": "director", "min_approvers": 1, "parallel": false},
    #   {"level": 3, "role": "cfo", "min_approvers": 1, "parallel": true}
    # ]
    
    requires_ipc = models.BooleanField(
        default=False,
        help_text="Requires IPC (Internal Purchase Committee) approval"
    )
    requires_cipc = models.BooleanField(
        default=False,
        help_text="Requires CIPC (Corporate Internal Purchase Committee) approval"
    )
    
    is_active = models.BooleanField(default=True, db_index=True)
    priority = models.IntegerField(default=100, help_text="Lower number = higher priority")
    
    class Meta:
        app_label = 'pr'
        verbose_name = 'Approval Chain'
        verbose_name_plural = 'Approval Chains'
        ordering = ['priority', 'name']
        indexes = [
            models.Index(fields=['condition_type', 'is_active']),
            models.Index(fields=['min_amount', 'max_amount']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_condition_type_display()})"
    
    def get_applicable_approvers(self, amount, pr_type=None):
        """
        Get list of approvers for given amount and PR type
        Returns list of (approval_level, required_roles, min_approvers)
        """
        if not self.is_active:
            return []
        
        # Check amount range
        if self.min_amount and amount < self.min_amount:
            return []
        if self.max_amount and amount > self.max_amount:
            return []
        
        # Check PR type if specified
        if pr_type and self.pr_types.exists():
            if not self.pr_types.filter(pk=pr_type.pk).exists():
                return []
        
        return self.approval_sequence
    
    @staticmethod
    def get_applicable_chains(amount, pr_type=None):
        """Get all applicable approval chains for amount and type"""
        chains = ApprovalChain.objects.filter(is_active=True).order_by('priority')
        applicable = []
        
        for chain in chains:
            approvers = chain.get_applicable_approvers(amount, pr_type)
            if approvers:
                applicable.append(chain)
        
        return applicable


class PurchaseRequisition(AuditableModel):
    """Main PR entity"""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pr_created', 'PR Created'),
        ('closed', 'Closed'),
    )
    
    # Unique identifier
    pr_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Format: PR/MM/YYYY/XXX"
    )
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    
    # Basic Information
    requester = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='pr_requested'
    )
    pr_type = models.ForeignKey(PRType, on_delete=models.PROTECT)
    department = models.CharField(max_length=100, db_index=True)
    
    # Description
    purpose_of_requirement = models.TextField(
        help_text="Detailed description of requirement"
    )
    request_date = models.DateField(auto_now_add=True)
    
    # Approval fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    approval_chain = models.ForeignKey(
        ApprovalChain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requisitions'
    )
    
    # Location & Plant
    plant = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Additional fields
    end_user_name = models.CharField(max_length=200, blank=True)
    end_user_department = models.CharField(max_length=100, blank=True)
    
    # IPC/CIPC Approval
    ipc_approval = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True
    )
    cipc_approval = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        blank=True
    )
    
    # CR (Capital Requisition) fields - for CAPEX
    cr_copy = models.CharField(max_length=100, blank=True)
    
    # Calculation fields
    grand_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Timestamps
    submitted_date = models.DateTimeField(null=True, blank=True)
    approval_completed_date = models.DateTimeField(null=True, blank=True)
    pr_created_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'pr'
        verbose_name = 'Purchase Requisition'
        verbose_name_plural = 'Purchase Requisitions'
        indexes = [
            models.Index(fields=['pr_number']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['approval_chain', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.pr_number} - {self.purpose_of_requirement[:50]}"
    
    def get_next_approvers(self):
        """Get the next level approvers for this PR"""
        if not self.approval_chain:
            return []
        
        # Get current approval level
        current_level = self.approvals.filter(
            approved_by__isnull=False
        ).aggregate(models.Max('approval_level'))['approval_level__max'] or 0
        
        next_level_data = None
        for level_data in self.approval_chain.approval_sequence:
            if level_data['level'] == current_level + 1:
                next_level_data = level_data
                break
        
        if not next_level_data:
            return []
        
        # Get users with required role
        role = Role.objects.filter(name=next_level_data['role']).first()
        if not role:
            return []
        
        approvers = UserProfile.objects.filter(
            role=role,
            is_approver=True,
            approval_limit__gte=self.grand_total,
            is_active=True
        ).select_related('user')
        
        return approvers
    
    def can_submit(self):
        """Check if PR can be submitted"""
        return self.status == 'draft' and self.pritem_set.exists()
    
    def can_be_approved(self, user):
        """Check if PR can be approved by user"""
        if self.status not in ['submitted', 'pending_approval']:
            return False
        
        if not hasattr(user, 'profile'):
            return False
        
        return user.profile.can_approve_amount(self.grand_total)


class PRItem(AuditableModel):
    """PR Line Items"""
    
    pr = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE
    )
    item_number = models.IntegerField()
    short_text = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    unit = models.CharField(max_length=20, default='PC')
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    total_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # CAPEX specific fields
    asset_code = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    gl_account = models.CharField(max_length=100, blank=True)
    
    class Meta:
        app_label = 'pr'
        verbose_name = 'PR Item'
        verbose_name_plural = 'PR Items'
        unique_together = ['pr', 'item_number']
        indexes = [
            models.Index(fields=['pr', 'item_number']),
        ]
    
    def __str__(self):
        return f"PR {self.pr.pr_number} - Item {self.item_number}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_value
        if self.quantity and self.unit_price:
            self.total_value = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class PRApproval(AuditableModel):
    """PR Approval Workflow"""
    
    APPROVAL_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
    )
    
    pr = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    approval_level = models.IntegerField()
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='pr_approvals_assigned'
    )
    status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS,
        default='pending',
        db_index=True
    )
    
    # Approval details
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pr_approvals_approved'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    
    # Timeline
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'pr'
        verbose_name = 'PR Approval'
        verbose_name_plural = 'PR Approvals'
        unique_together = ['pr', 'approval_level']
        indexes = [
            models.Index(fields=['pr', 'approval_level']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.pr.pr_number} - Level {self.approval_level}"


class PRStatus(AuditableModel):
    """Track PR status transitions"""
    
    pr = models.ForeignKey(
        PurchaseRequisition,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        app_label = 'pr'
        verbose_name = 'PR Status'
        verbose_name_plural = 'PR Status History'
        indexes = [
            models.Index(fields=['pr', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.pr.pr_number}: {self.from_status} → {self.to_status}"
