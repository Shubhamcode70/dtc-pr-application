"""
Context processors for user permissions in templates
"""

from apps.users.permissions import (
    is_admin, is_manager, is_requester, is_approver, is_finance
)


def user_permissions(request):
    """Add user permissions to template context"""
    if not request.user.is_authenticated:
        return {
            'user_is_admin': False,
            'user_is_manager': False,
            'user_is_requester': False,
            'user_is_approver': False,
            'user_is_finance': False,
            'user_role': None,
            'user_approval_limit': 0,
        }
    
    return {
        'user_is_admin': is_admin(request.user),
        'user_is_manager': is_manager(request.user),
        'user_is_requester': is_requester(request.user),
        'user_is_approver': is_approver(request.user),
        'user_is_finance': is_finance(request.user),
        'user_role': request.user.profile.role if hasattr(request.user, 'profile') else None,
        'user_approval_limit': request.user.profile.approval_limit if hasattr(request.user, 'profile') else 0,
    }
