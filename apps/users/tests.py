"""Tests for Users and Authentication"""

from django.test import TestCase
from django.contrib.auth.models import User
from apps.users.models import Role, UserProfile
from apps.users.permissions import (
    has_role, is_admin, is_approver, has_any_role
)


class RoleTestCase(TestCase):
    """Test Role model"""
    
    def setUp(self):
        self.admin_role = Role.objects.create(
            name='admin',
            description='Administrator'
        )
        self.requester_role = Role.objects.create(
            name='requester',
            description='Requester'
        )
    
    def test_role_creation(self):
        """Test creating a role"""
        self.assertEqual(self.admin_role.name, 'admin')
        self.assertTrue(self.admin_role.is_active)
    
    def test_role_str(self):
        """Test role string representation"""
        self.assertEqual(str(self.admin_role), 'Administrator')


class UserProfileTestCase(TestCase):
    """Test UserProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_role = Role.objects.create(name='admin')
        self.approver_role = Role.objects.create(name='approver')
    
    def test_user_profile_creation(self):
        """Test user profile is created automatically"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsNotNone(self.user.profile)
    
    def test_user_profile_with_role(self):
        """Test user profile with role assignment"""
        profile = self.user.profile
        profile.role = self.admin_role
        profile.save()
        
        self.assertEqual(profile.role.name, 'admin')
    
    def test_approval_authority(self):
        """Test approval authority check"""
        profile = self.user.profile
        profile.role = self.approver_role
        profile.is_approver = True
        profile.approval_limit = 100000
        profile.save()
        
        self.assertTrue(profile.has_approval_authority)
        self.assertTrue(profile.can_approve_amount(50000))
        self.assertFalse(profile.can_approve_amount(150000))


class RBACPermissionTestCase(TestCase):
    """Test RBAC permission checks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_role = Role.objects.create(name='admin')
        self.user.profile.role = self.admin_role
        self.user.profile.save()
    
    def test_has_role(self):
        """Test has_role function"""
        self.assertTrue(has_role(self.user, 'admin'))
        self.assertFalse(has_role(self.user, 'requester'))
    
    def test_is_admin(self):
        """Test is_admin function"""
        self.assertTrue(is_admin(self.user))
    
    def test_has_any_role(self):
        """Test has_any_role function"""
        self.assertTrue(has_any_role(self.user, ['admin', 'manager']))
        self.assertFalse(has_any_role(self.user, ['requester', 'finance']))
