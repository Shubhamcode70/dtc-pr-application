"""
Admin configuration for Users app
"""

from django.contrib import admin
from django.contrib.auth.models import User
from apps.users.models import Role, UserProfile, PermissionGroup, LoginAttempt
from apps.core.admin import BaseModelAdmin


@admin.register(Role)
class RoleAdmin(BaseModelAdmin):
    list_display = ('name', 'get_description_short', 'is_active', 'created_at')
    list_filter = ('name', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    
    def get_description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    get_description_short.short_description = 'Description'


@admin.register(UserProfile)
class UserProfileAdmin(BaseModelAdmin):
    list_display = ('user', 'role', 'department', 'is_approver', 'approval_limit', 'is_active')
    list_filter = ('role', 'department', 'is_approver', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'employee_id')
    readonly_fields = ('user', 'created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'department', 'employee_id')
        }),
        ('Contact Information', {
            'fields': ('phone', 'location')
        }),
        ('Approval Settings', {
            'fields': ('is_approver', 'approval_limit', 'manager')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted')
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PermissionGroup)
class PermissionGroupAdmin(BaseModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('roles',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(BaseModelAdmin):
    list_display = ('user', 'success', 'ip_address', 'created_at')
    list_filter = ('success', 'created_at')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'success', 'reason', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
