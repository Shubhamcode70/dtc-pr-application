"""
User and Authentication Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.core.paginator import Paginator
from apps.users.models import UserProfile, Role
from apps.users.permissions import require_admin
import logging

logger = logging.getLogger(__name__)


# API Views for Authentication

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info(f"User {username} logged in successfully")
            return redirect('dashboard:dashboard')
        else:
            logger.warning(f"Failed login attempt for user {username}")
            return render(request, 'auth/login.html', {
                'error': 'Invalid username or password'
            })
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """User logout view"""
    username = request.user.username if request.user.is_authenticated else 'Unknown'
    logout(request)
    logger.info(f"User {username} logged out")
    return redirect('auth:login')


@login_required
def user_profile_view(request):
    """View user profile"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'users/profile.html', {
        'user_profile': user_profile
    })


@login_required
@require_admin
def user_management_view(request):
    """Admin: User management page"""
    users = User.objects.filter(is_active=True).select_related('profile__role')
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/management.html', {
        'page_obj': page_obj,
        'users': page_obj.object_list
    })


@login_required
@require_admin
def user_edit_view(request, user_id):
    """Admin: Edit user role and permissions"""
    user = get_object_or_404(User, pk=user_id)
    user_profile = get_object_or_404(UserProfile, user=user)
    roles = Role.objects.filter(is_active=True)
    
    if request.method == 'POST':
        role_id = request.POST.get('role')
        is_approver = request.POST.get('is_approver') == 'on'
        approval_limit = request.POST.get('approval_limit', 0)
        
        user_profile.role = get_object_or_404(Role, pk=role_id)
        user_profile.is_approver = is_approver
        user_profile.approval_limit = float(approval_limit) if approval_limit else 0
        user_profile.save()
        
        logger.info(f"Admin updated user {user.username} profile")
        return redirect('auth:management')
    
    return render(request, 'users/edit.html', {
        'user': user,
        'user_profile': user_profile,
        'roles': roles
    })


@login_required
def get_user_permissions(request):
    """Get current user's permissions as JSON"""
    user = request.user
    permissions = {
        'is_authenticated': user.is_authenticated,
        'is_admin': user.is_superuser,
        'role': user.profile.role.name if hasattr(user, 'profile') and user.profile.role else None,
        'is_approver': user.profile.is_approver if hasattr(user, 'profile') else False,
        'approval_limit': str(user.profile.approval_limit) if hasattr(user, 'profile') else '0',
        'department': user.profile.department if hasattr(user, 'profile') else None,
    }
    return JsonResponse(permissions)


# REST API Views (for AJAX calls)

def api_check_username(request):
    """Check if username is available"""
    username = request.GET.get('username', '')
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({
        'available': not exists,
        'username': username
    })


@login_required
def api_get_approvers(request):
    """Get list of approvers for a given amount"""
    amount = float(request.GET.get('amount', 0))
    
    approvers = UserProfile.objects.filter(
        is_approver=True,
        approval_limit__gte=amount,
        is_active=True
    ).select_related('user').values_list('user__id', 'user__get_full_name', 'approval_limit')
    
    data = [
        {
            'id': approver[0],
            'name': approver[1],
            'limit': str(approver[2])
        }
        for approver in approvers
    ]
    
    return JsonResponse({
        'approvers': data,
        'count': len(data)
    })
