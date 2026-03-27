"""
Project Initialization Script
Run this after migrations to set up initial data
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth.models import User
from apps.users.models import Role
from apps.pr.models import PRType, ApprovalChain


def create_roles():
    """Create default roles"""
    print("Creating roles...")
    roles_data = [
        ('admin', 'Administrator - Full system access'),
        ('manager', 'Manager - Can approve PRs up to defined limits'),
        ('requester', 'Requester - Can create and submit PRs'),
        ('approver', 'Approver - Can approve PRs'),
        ('finance', 'Finance Officer - Can view all PRs and generate reports'),
    ]
    
    for name, description in roles_data:
        role, created = Role.objects.get_or_create(
            name=name,
            defaults={'description': description, 'is_active': True}
        )
        status = "Created" if created else "Already exists"
        print(f"  ✓ {name}: {status}")
    
    print(f"Total roles: {Role.objects.count()}")


def create_pr_types():
    """Create PR types"""
    print("\nCreating PR types...")
    pr_types = [
        ('CAPEX', 'Capital Expenditure', 'capex', 'For asset purchases > 5 Lakhs'),
        ('OPEX', 'Operating Expenditure', 'opex', 'For regular operational expenses'),
        ('MAINT', 'Maintenance', 'maintenance', 'For maintenance and repairs'),
        ('SERVICE', 'Service', 'service', 'For service procurements'),
    ]
    
    for code, name, type_choice, description in pr_types:
        pr_type, created = PRType.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'type': type_choice,
                'description': description,
                'is_active': True
            }
        )
        status = "Created" if created else "Already exists"
        print(f"  ✓ {code}: {status}")
    
    print(f"Total PR types: {PRType.objects.count()}")


def create_approval_chains():
    """Create approval chains"""
    print("\nCreating approval chains...")
    
    # Chain 1: < 1 Million (Manager approval)
    chain1, created = ApprovalChain.objects.get_or_create(
        name='Small Purchase (< 10 Lakhs)',
        defaults={
            'description': 'For purchases less than 10 Lakhs',
            'condition_type': 'amount_range',
            'min_amount': Decimal('0'),
            'max_amount': Decimal('1000000'),
            'approval_sequence': [
                {
                    'level': 1,
                    'role': 'manager',
                    'min_approvers': 1,
                    'parallel': False,
                    'description': 'Manager approval required'
                }
            ],
            'requires_ipc': False,
            'requires_cipc': False,
            'is_active': True,
            'priority': 10
        }
    )
    print(f"  ✓ Chain 1 (< 10L): {'Created' if created else 'Already exists'}")
    
    # Chain 2: 1M - 10M (Manager + Director)
    chain2, created = ApprovalChain.objects.get_or_create(
        name='Medium Purchase (10L - 1Cr)',
        defaults={
            'description': 'For purchases between 10 Lakhs and 1 Crore',
            'condition_type': 'amount_range',
            'min_amount': Decimal('1000000'),
            'max_amount': Decimal('10000000'),
            'approval_sequence': [
                {
                    'level': 1,
                    'role': 'manager',
                    'min_approvers': 1,
                    'parallel': False
                },
                {
                    'level': 2,
                    'role': 'approver',
                    'min_approvers': 1,
                    'parallel': False
                }
            ],
            'requires_ipc': True,
            'requires_cipc': False,
            'is_active': True,
            'priority': 20
        }
    )
    print(f"  ✓ Chain 2 (10L - 1Cr): {'Created' if created else 'Already exists'}")
    
    # Chain 3: > 10M (Requires CIPC approval)
    chain3, created = ApprovalChain.objects.get_or_create(
        name='Large Purchase (> 1Cr)',
        defaults={
            'description': 'For purchases greater than 1 Crore',
            'condition_type': 'amount_range',
            'min_amount': Decimal('10000000'),
            'max_amount': None,  # No upper limit
            'approval_sequence': [
                {
                    'level': 1,
                    'role': 'manager',
                    'min_approvers': 1,
                    'parallel': False
                },
                {
                    'level': 2,
                    'role': 'approver',
                    'min_approvers': 2,
                    'parallel': False
                }
            ],
            'requires_ipc': True,
            'requires_cipc': True,
            'is_active': True,
            'priority': 30
        }
    )
    print(f"  ✓ Chain 3 (> 1Cr): {'Created' if created else 'Already exists'}")
    
    print(f"Total approval chains: {ApprovalChain.objects.count()}")


def create_superuser():
    """Create superuser if doesn't exist"""
    print("\nSuperuser check...")
    if User.objects.filter(username='admin').exists():
        print("  ✓ Superuser 'admin' already exists")
    else:
        print("  ! Superuser 'admin' not found. Creating...")
        user = User.objects.create_superuser(
            username='admin',
            email='admin@dtcpr.local',
            password='admin123'
        )
        print(f"  ✓ Superuser created: {user.username}")
        print("  ⚠️  DEFAULT PASSWORD DETECTED - Change immediately in production!")


def display_summary():
    """Display initialization summary"""
    print("\n" + "="*60)
    print("PROJECT INITIALIZATION COMPLETE")
    print("="*60)
    print(f"\n✓ Roles: {Role.objects.count()}")
    print(f"✓ PR Types: {PRType.objects.count()}")
    print(f"✓ Approval Chains: {ApprovalChain.objects.count()}")
    print(f"✓ Users: {User.objects.count()}")
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Run Django development server:")
    print("   python manage.py runserver")
    print("\n2. Login to admin panel:")
    print("   http://localhost:8000/admin/")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n3. Assign roles to users in admin panel")
    print("\n4. Create approval chain rules for your organization")
    print("\n5. Configure email settings for notifications (when ready)")
    print("\n" + "="*60)


if __name__ == '__main__':
    try:
        create_roles()
        create_pr_types()
        create_approval_chains()
        create_superuser()
        display_summary()
        print("\n✅ Initialization completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
