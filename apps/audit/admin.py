from django.contrib import admin
from apps.audit.models import AuditLog, ActivityLog, ApprovalHistory


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'model_name', 'created_at', 'success')
    list_filter = ('action', 'success', 'created_at')
    search_fields = ('user__username', 'model_name', 'description')
    readonly_fields = ('action', 'user', 'model_name', 'created_at', 'ip_address')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('pr', 'event', 'user', 'created_at')
    list_filter = ('event', 'created_at')
    search_fields = ('pr__pr_number', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(ApprovalHistory)
class ApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = ('pr', 'approval_level', 'status', 'assigned_to')
    list_filter = ('status', 'created_at')
    search_fields = ('pr__pr_number', 'assigned_to__username')
