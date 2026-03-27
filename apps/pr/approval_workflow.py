"""
Approval workflow engine for handling PR approvals based on ApprovalChain rules.
Implements rule-based approval logic with amount thresholds and role-based approvers.
"""

from decimal import Decimal
from typing import List, Dict, Tuple
from django.contrib.auth import get_user_model
from .models import ApprovalChain, PRApproval, PurchaseRequisition

User = get_user_model()


class ApprovalWorkflowEngine:
    """Engine for determining and managing approval chains based on PR characteristics."""
    
    # Default approval thresholds in rupees
    APPROVAL_THRESHOLDS = {
        'CAPEX': [
            (Decimal('100000'), 'Requester'),      # < 1 Lakh
            (Decimal('1000000'), 'Manager'),       # < 10 Lakhs
            (Decimal('10000000'), 'Director'),     # < 1 Crore
            (Decimal('float("inf")'), 'CFO'),       # >= 1 Crore
        ],
        'OPEX': [
            (Decimal('50000'), 'Requester'),       # < 50K
            (Decimal('500000'), 'Manager'),        # < 5 Lakhs
            (Decimal('5000000'), 'Finance_Head'),  # < 50 Lakhs
            (Decimal('float("inf")'), 'CFO'),      # >= 50 Lakhs
        ]
    }
    
    def __init__(self, pr: PurchaseRequisition):
        """Initialize with a PurchaseRequisition instance."""
        self.pr = pr
        self.total_value = self._calculate_total_value()
    
    def _calculate_total_value(self) -> Decimal:
        """Calculate total PR value from all items."""
        from django.db.models import Sum, F
        result = self.pr.items.aggregate(
            total=Sum(F('quantity') * F('unit_price'), output_field=Decimal)
        )
        return result['total'] or Decimal('0')
    
    def get_required_approvers(self) -> List[Dict]:
        """
        Determine list of approvers required based on PR value and type.
        
        Returns:
            List of dicts with approver roles and user information
        """
        approvers = []
        pr_type = self.pr.pr_type
        
        # Get appropriate thresholds for PR type
        thresholds = self.APPROVAL_THRESHOLDS.get(pr_type, [])
        
        if not thresholds:
            # Default fallback
            thresholds = self.APPROVAL_THRESHOLDS['OPEX']
        
        # Find applicable approvers based on value
        for threshold, role_name in thresholds:
            if self.total_value <= threshold:
                approvers.append({
                    'role_name': role_name,
                    'description': f'Approval required for {pr_type} > {threshold}',
                })
                break
        
        # Add IPC/CIPC approvals if required
        if self.pr.ipc_approval_required:
            approvers.append({
                'role_name': 'IPC_Committee',
                'description': 'IPC (Internal Purchase Committee) Approval'
            })
        
        if self.pr.cipc_approval_required:
            approvers.append({
                'role_name': 'CIPC_Committee',
                'description': 'CIPC (Committee) Approval'
            })
        
        return approvers
    
    def create_approval_chain(self) -> List[PRApproval]:
        """
        Create approval chain for this PR with all required approvers.
        
        Returns:
            List of created PRApproval objects
        """
        from apps.users.models import Role
        
        approvals = []
        required_approvers = self.get_required_approvers()
        sequence = 1
        
        for approver_spec in required_approvers:
            role_name = approver_spec['role_name']
            
            # Get users with this role (for now, get first user with role)
            try:
                role = Role.objects.get(name=role_name)
                users = User.objects.filter(role=role)
                
                if users.exists():
                    approver = users.first()
                    approval = PRApproval.objects.create(
                        purchase_requisition=self.pr,
                        approver=approver,
                        sequence=sequence,
                        approval_status='PENDING'
                    )
                    approvals.append(approval)
                    sequence += 1
            except Role.DoesNotExist:
                # Log missing role
                print(f"Warning: Role '{role_name}' not found in database")
        
        return approvals
    
    def can_proceed_to_next_level(self) -> Tuple[bool, str]:
        """
        Check if current approval level is complete and PR can proceed to next.
        
        Returns:
            Tuple of (can_proceed: bool, message: str)
        """
        pending_approvals = self.pr.approvals.filter(approval_status='PENDING')
        
        if not pending_approvals.exists():
            return True, "All approvals complete"
        
        # Check if current sequence level is complete
        current_sequence = pending_approvals.order_by('sequence').first().sequence
        current_level_approvals = self.pr.approvals.filter(sequence=current_sequence)
        
        approved_count = current_level_approvals.filter(
            approval_status='APPROVED'
        ).count()
        
        if approved_count == current_level_approvals.count():
            return True, f"Level {current_sequence} complete, ready for next level"
        
        remaining = current_level_approvals.filter(
            approval_status='PENDING'
        ).count()
        
        return False, f"Waiting for {remaining} approvals at level {current_sequence}"
    
    def get_approval_status_summary(self) -> Dict:
        """Get summary of approval status."""
        approvals = self.pr.approvals.all()
        
        summary = {
            'total_required': approvals.count(),
            'approved': approvals.filter(approval_status='APPROVED').count(),
            'rejected': approvals.filter(approval_status='REJECTED').count(),
            'pending': approvals.filter(approval_status='PENDING').count(),
            'approval_chain': []
        }
        
        for approval in approvals.order_by('sequence'):
            summary['approval_chain'].append({
                'sequence': approval.sequence,
                'approver': approval.approver.get_full_name(),
                'status': approval.approval_status,
                'approval_date': approval.approval_date,
                'comments': approval.comments
            })
        
        return summary
    
    def reject_pr(self, reason: str = None) -> bool:
        """
        Reject the entire PR (any rejection at any level rejects the PR).
        
        Args:
            reason: Optional reason for rejection
            
        Returns:
            bool: Success status
        """
        self.pr.status = 'REJECTED'
        self.pr.rejection_reason = reason or 'Rejected by approver'
        self.pr.save()
        return True
    
    def approve_and_move_forward(self) -> Tuple[bool, str]:
        """
        Approve current level and move to next if all approvals at current level are done.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        can_proceed, message = self.can_proceed_to_next_level()
        
        if not can_proceed:
            return False, message
        
        # Check if all approvals are complete
        if self.pr.approvals.filter(approval_status='PENDING').exists():
            return True, "Current level approved, awaiting next level"
        
        # All approvals complete
        self.pr.status = 'APPROVED'
        self.pr.save()
        
        return True, "All approvals complete, PR approved"


class ApprovalChainBuilder:
    """Builder class for creating and managing ApprovalChain configurations."""
    
    @staticmethod
    def create_default_chains():
        """Create default approval chain configurations."""
        chains = []
        
        # CAPEX < 1 Lakh
        chain1 = ApprovalChain.objects.create(
            name='CAPEX - < 1 Lakh',
            description='CAPEX purchase less than 1 Lakh',
            pr_type='CAPEX',
            min_amount=0,
            max_amount=100000,
            required_approvals=1,
            approver_roles='Requester,Manager'
        )
        chains.append(chain1)
        
        # CAPEX 1-10 Lakh
        chain2 = ApprovalChain.objects.create(
            name='CAPEX - 1-10 Lakh',
            description='CAPEX purchase between 1-10 Lakh',
            pr_type='CAPEX',
            min_amount=100000,
            max_amount=1000000,
            required_approvals=2,
            approver_roles='Manager,Director'
        )
        chains.append(chain2)
        
        # OPEX < 50K
        chain3 = ApprovalChain.objects.create(
            name='OPEX - < 50K',
            description='OPEX purchase less than 50K',
            pr_type='OPEX',
            min_amount=0,
            max_amount=50000,
            required_approvals=1,
            approver_roles='Manager'
        )
        chains.append(chain3)
        
        return chains
