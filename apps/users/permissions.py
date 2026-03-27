"""
RBAC Permission Decorators and Utilities
"""

from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.http import HttpResponseForbidden


def get_user_role(user):
    """Get the role of a user"""
    if not user.is_authenticated:
        return None
    if hasattr(user, 'profile'):
        return user.profile.role
    return None


def has_role(user, role_name):
    """Check if user has a specific role"""
    user_role = get_user_role(user)
    if user_role is None:
        return False
    return user_role.name == role_name


def has_any_role(user, role_names):
    """Check if user has any of the given roles"""
    user_role = get_user_role(user)
    if user_role is None:
        return False
    return user_role.name in role_names


def is_admin(user):
    """Check if user is admin"""
    return user.is_superuser or has_role(user, 'admin')


def is_manager(user):
    """Check if user is manager"""
    return has_role(user, 'manager')


def is_requester(user):
    """Check if user is requester"""
    return has_role(user, 'requester')


def is_approver(user):
    """Check if user is approver"""
    if hasattr(user, 'profile'):
        return user.profile.is_approver
    return False


def is_finance(user):
    """Check if user is finance officer"""
    return has_role(user, 'finance')


# Decorators for views

def require_role(role_name):
    """Decorator to require a specific role"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_role(request.user, role_name):
                raise PermissionDenied("You do not have permission to access this resource.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_role(*role_names):
    """Decorator to require any of the given roles"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_any_role(request, role_names):
                raise PermissionDenied("You do not have permission to access this resource.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_admin(view_func):
    """Decorator to require admin role"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied("You do not have permission to access this resource.")
        return view_func(request, *args, **kwargs)
    return wrapper


def require_approver(view_func):
    """Decorator to require approver role"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_approver(request.user):
            raise PermissionDenied("You do not have permission to approve requests.")
        return view_func(request, *args, **kwargs)
    return wrapper


def require_approval_amount(required_amount):
    """Decorator to check if user can approve a specific amount"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                raise PermissionDenied("User profile not found.")
            
            profile = request.user.profile
            if not profile.can_approve_amount(required_amount):
                raise PermissionDenied(
                    f"You are not authorized to approve amounts of {required_amount}. "
                    f"Your approval limit is {profile.approval_limit}."
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class RolePermissionMixin:
    """Mixin for class-based views to check roles"""
    
    required_roles = []
    require_all_roles = False
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user_roles = [request.user.profile.role.name] if hasattr(request.user, 'profile') else []
        
        if self.require_all_roles:
            has_permission = all(role in user_roles for role in self.required_roles)
        else:
            has_permission = any(role in user_roles for role in self.required_roles)
        
        if not has_permission:
            raise PermissionDenied("You do not have permission to access this resource.")
        
        return super().dispatch(request, *args, **kwargs)
