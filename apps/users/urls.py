"""
Users App URLs
"""

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.user_profile_view, name='profile'),
    path('management/', views.user_management_view, name='management'),
    path('edit/<int:user_id>/', views.user_edit_view, name='edit'),
    path('permissions/', views.get_user_permissions, name='permissions'),
    path('check-username/', views.api_check_username, name='check_username'),
    path('approvers/', views.api_get_approvers, name='approvers'),
]
