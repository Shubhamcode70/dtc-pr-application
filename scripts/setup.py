"""
Database and initial data setup script for DTC PR Application.
Run: python manage.py shell < scripts/setup.py
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import Role, Permission, UserRole
from apps.pr.models import ApprovalChain
from apps.pr.approval_workflow import ApprovalChainBuilder

User = get_user_model()

def create_roles():
    """Create default roles."""
    print("Creating roles...")
    
    roles_data = [
        {
            'name': 'Admin',
            'description': 'Full access to the system',
            'permissions': [
                'create_pr', 'edit_pr', 'delete_pr', 'approve_pr',
                'view_audit', 'manage_users', 'manage_vendors'
            ]
        },
        {
            'name': 'Manager',
            'description': 'Can manage and approve PRs',
            'permissions': ['create_pr', 'edit_pr', 'approve_pr', 'view_reports']
        },
        {
            'name': 'Requester',
            'description': 'Can create and view their own PRs',
            'permissions': ['create_pr', 'edit_own_pr', 'view_own_pr']
        },
        {
            'name': 'Approver',
            'description': 'Can approve PRs',
            'permissions': ['approve_pr', 'view_pr', 'add_comments']
        },
        {
            'name': 'Finance',
            'description': 'Finance department access',
            'permissions': ['view_pr', 'view_reports', 'export_data']
        },
        {
            'name': 'IPC_Committee',
            'description': 'IPC Committee member',
            'permissions': ['approve_pr', 'view_pr']
        },
        {
            'name': 'CIPC_Committee',
            'description': 'CIPC Committee member',
            'permissions': ['approve_pr', 'view_pr']
        },
    ]
    
    for role_data in roles_data:
        role, created = Role.objects.get_or_create(name=role_data['name'])
        role.description = role_data['description']
        role.save()
        
        # Add permissions
        for perm_name in role_data['permissions']:
            perm, _ = Permission.objects.get_or_create(
                name=perm_name,
                defaults={'description': perm_name.replace('_', ' ').title()}
            )
            role.permissions.add(perm)
        
        print(f"  ✓ Created role: {role.name}")
    
    print("Roles created successfully!\n")


def create_approval_chains():
    """Create default approval chain configurations."""
    print("Creating approval chains...")
    
    # Use the builder to create default chains
    chains = ApprovalChainBuilder.create_default_chains()
    
    for chain in chains:
        print(f"  ✓ Created approval chain: {chain.name}")
    
    print("Approval chains created successfully!\n")


def create_test_users():
    """Create test users for different roles."""
    print("Creating test users...")
    
    test_users = [
        {
            'email': 'requester@example.com',
            'first_name': 'John',
            'last_name': 'Requester',
            'role': 'Requester'
        },
        {
            'email': 'manager@example.com',
            'first_name': 'Jane',
            'last_name': 'Manager',
            'role': 'Manager'
        },
        {
            'email': 'approver@example.com',
            'first_name': 'Bob',
            'last_name': 'Approver',
            'role': 'Approver'
        },
        {
            'email': 'finance@example.com',
            'first_name': 'Alice',
            'last_name': 'Finance',
            'role': 'Finance'
        },
        {
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'Admin'
        },
    ]
    
    for user_data in test_users:
        email = user_data['email']
        
        if User.objects.filter(email=email).exists():
            print(f"  - User {email} already exists, skipping...")
            continue
        
        user = User.objects.create_user(
            email=email,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            password='TestPassword123!'
        )
        
        # Assign role
        role = Role.objects.get(name=user_data['role'])
        user.role = role
        user.save()
        
        print(f"  ✓ Created user: {email} (Role: {user_data['role']})")
    
    print("Test users created successfully!\n")


def print_summary():
    """Print setup summary."""
    print("\n" + "="*60)
    print("DTC PR APPLICATION - SETUP COMPLETED")
    print("="*60)
    
    print(f"\nRoles: {Role.objects.count()}")
    print(f"Permissions: {Permission.objects.count()}")
    print(f"Users: {User.objects.count()}")
    print(f"Approval Chains: {ApprovalChain.objects.count()}")
    
    print("\nTest Users:")
    for user in User.objects.all():
        print(f"  - {user.email} (Role: {user.role.name if user.role else 'None'})")
    
    print("\nNext Steps:")
    print("1. Run: python manage.py runserver")
    print("2. Access: http://localhost:8000/admin")
    print("3. Login with: admin@example.com / TestPassword123!")
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    try:
        create_roles()
        create_approval_chains()
        create_test_users()
        print_summary()
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        raise
