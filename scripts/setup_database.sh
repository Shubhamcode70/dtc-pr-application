#!/bin/bash

# Database setup script for DTC PR Application
# This script initializes the PostgreSQL database and runs migrations

set -e

echo "Starting database setup for DTC PR Application..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and update with your settings."
    exit 1
fi

# Create migrations for all apps
echo "Creating migrations..."
python manage.py makemigrations core
python manage.py makemigrations users
python manage.py makemigrations pr
python manage.py makemigrations vendor
python manage.py makemigrations attachments
python manage.py makemigrations audit
python manage.py makemigrations notifications
python manage.py makemigrations dashboard

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Create superuser
echo "Creating superuser..."
python manage.py createsuperuser

# Create default roles
echo "Creating default roles..."
python manage.py shell << END
from apps.users.models import Role, Permission

# Create roles
roles_data = [
    {
        'name': 'Admin',
        'description': 'Full access to the system',
        'permissions': ['create_pr', 'edit_pr', 'delete_pr', 'approve_pr', 'view_audit', 'manage_users', 'manage_vendors']
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
    
    print(f"Created role: {role.name}")

print("Database setup completed successfully!")
END

echo "Database setup completed!"
