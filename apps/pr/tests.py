"""Tests for PR Models and Services"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from apps.pr.models import (
    PRType, ApprovalChain, PurchaseRequisition, PRItem, PRApproval
)
from apps.pr.services import PRService, ApprovalChainService
from apps.users.models import Role, UserProfile
from decimal import Decimal


class PRTypeTestCase(TestCase):
    """Test PR Type model"""
    
    def setUp(self):
        self.pr_type = PRType.objects.create(
            code='CAPEX',
            name='Capital Expenditure',
            type='capex'
        )
    
    def test_pr_type_creation(self):
        """Test creating a PR type"""
        self.assertEqual(self.pr_type.code, 'CAPEX')
        self.assertEqual(self.pr_type.type, 'capex')
    
    def test_pr_type_str(self):
        """Test PR type string representation"""
        self.assertEqual(str(self.pr_type), 'CAPEX - Capital Expenditure')


class ApprovalChainTestCase(TestCase):
    """Test ApprovalChain model - CRITICAL"""
    
    def setUp(self):
        self.chain = ApprovalChain.objects.create(
            name='Standard Approval Chain',
            description='For amounts < 1 Million',
            condition_type='amount_range',
            min_amount=Decimal('0'),
            max_amount=Decimal('1000000'),
            approval_sequence=[
                {'level': 1, 'role': 'manager', 'min_approvers': 1, 'parallel': False},
                {'level': 2, 'role': 'director', 'min_approvers': 1, 'parallel': False}
            ],
            is_active=True
        )
    
    def test_approval_chain_creation(self):
        """Test creating an approval chain"""
        self.assertEqual(self.chain.name, 'Standard Approval Chain')
        self.assertTrue(self.chain.is_active)
    
    def test_approval_chain_amount_range(self):
        """Test approval chain amount range validation"""
        # Within range
        approvers = self.chain.get_applicable_approvers(Decimal('500000'))
        self.assertEqual(len(approvers), 2)
        
        # Below minimum
        approvers = self.chain.get_applicable_approvers(Decimal('-100'))
        self.assertEqual(len(approvers), 0)
        
        # Above maximum
        approvers = self.chain.get_applicable_approvers(Decimal('2000000'))
        self.assertEqual(len(approvers), 0)
    
    def test_get_applicable_chains(self):
        """Test getting applicable chains for amount"""
        chains = ApprovalChain.get_applicable_chains(Decimal('500000'))
        self.assertIn(self.chain, chains)
    
    def test_approval_sequence_structure(self):
        """Test approval sequence structure"""
        seq = self.chain.approval_sequence
        self.assertEqual(len(seq), 2)
        self.assertEqual(seq[0]['level'], 1)
        self.assertEqual(seq[0]['role'], 'manager')


class PurchaseRequisitionTestCase(TestCase):
    """Test PurchaseRequisition model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='requester',
            password='testpass123'
        )
        self.pr_type = PRType.objects.create(
            code='OPEX',
            name='Operating Expenditure',
            type='opex'
        )
        self.pr = PurchaseRequisition.objects.create(
            pr_number='PR/01/2024/001',
            requester=self.user,
            pr_type=self.pr_type,
            department='Operations',
            purpose_of_requirement='Buy office supplies',
            created_by=self.user
        )
    
    def test_pr_creation(self):
        """Test creating a PR"""
        self.assertEqual(self.pr.status, 'draft')
        self.assertEqual(self.pr.requester.username, 'requester')
    
    def test_pr_number_uniqueness(self):
        """Test PR number is unique"""
        with self.assertRaises(Exception):
            PurchaseRequisition.objects.create(
                pr_number=self.pr.pr_number,
                requester=self.user,
                pr_type=self.pr_type,
                department='Operations',
                purpose_of_requirement='Another PR',
                created_by=self.user
            )
    
    def test_pr_str(self):
        """Test PR string representation"""
        self.assertIn(self.pr.pr_number, str(self.pr))


class PRItemTestCase(TestCase):
    """Test PRItem model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='requester',
            password='testpass123'
        )
        self.pr_type = PRType.objects.create(code='OPEX', name='OPEX', type='opex')
        self.pr = PurchaseRequisition.objects.create(
            pr_number='PR/01/2024/001',
            requester=self.user,
            pr_type=self.pr_type,
            department='Operations',
            purpose_of_requirement='Test PR',
            created_by=self.user
        )
    
    def test_pr_item_creation(self):
        """Test creating a PR item"""
        item = PRItem.objects.create(
            pr=self.pr,
            item_number=1,
            short_text='Test Item',
            quantity=Decimal('10'),
            unit='PC',
            unit_price=Decimal('100'),
            created_by=self.user
        )
        self.assertEqual(item.total_value, Decimal('1000'))
    
    def test_pr_item_auto_calculation(self):
        """Test auto-calculation of total_value"""
        item = PRItem.objects.create(
            pr=self.pr,
            item_number=1,
            quantity=Decimal('5'),
            unit_price=Decimal('200'),
            created_by=self.user
        )
        self.assertEqual(item.total_value, Decimal('1000'))


class PRServiceTestCase(TestCase):
    """Test PR Service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='requester',
            password='testpass123'
        )
        self.pr_type = PRType.objects.create(code='OPEX', name='OPEX', type='opex')
    
    def test_generate_pr_number(self):
        """Test PR number generation"""
        pr_num = PRService.generate_pr_number(self.pr_type)
        self.assertRegex(pr_num, r'PR/\d{2}/\d{4}/\d{3}')
    
    def test_create_pr(self):
        """Test creating PR via service"""
        pr = PRService.create_pr(
            requester=self.user,
            pr_type=self.pr_type,
            department='Operations',
            purpose='Test PR'
        )
        self.assertEqual(pr.status, 'draft')
        self.assertEqual(pr.requester, self.user)
