"""PR Admin Configuration"""

from django.contrib import admin
from apps.pr.models import (
    PRType, ApprovalChain, PurchaseRequisition, PRItem,
    PRApproval, PRStatus
)
from apps.core.admin import BaseModelAdmin


@admin.register(PRType)
class PRTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'type', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('code', 'name')


@admin.register(ApprovalChain)
class ApprovalChainAdmin(BaseModelAdmin):
    list_display = ('name', 'condition_type', 'priority', 'is_active')
    list_filter = ('condition_type', 'is_active', 'requires_ipc', 'requires_cipc')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'condition_type', 'is_active', 'priority')
        }),
        ('Amount Range', {
            'fields': ('min_amount', 'max_amount'),
        }),
        ('PR Types', {
            'fields': ('pr_types',),
        }),
        ('Approval Sequence', {
            'fields': ('approval_sequence', 'requires_ipc', 'requires_cipc'),
        }),
    )


class PRItemInline(admin.TabularInline):
    model = PRItem
    extra = 1
    fields = ('item_number', 'short_text', 'quantity', 'unit', 'unit_price', 'total_value')
    readonly_fields = ('total_value',)


@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(BaseModelAdmin):
    list_display = ('pr_number', 'requester', 'status', 'grand_total', 'created_at')
    list_filter = ('status', 'pr_type', 'created_at')
    search_fields = ('pr_number', 'requester__username')
    inlines = [PRItemInline]
    readonly_fields = ('pr_number', 'uuid', 'grand_total')
    
    fieldsets = (
        ('PR Information', {
            'fields': ('pr_number', 'uuid', 'pr_type', 'status', 'requester', 'department')
        }),
        ('Details', {
            'fields': ('purpose_of_requirement', 'plant', 'location', 'end_user_name', 'end_user_department')
        }),
        ('Approvals', {
            'fields': ('approval_chain', 'ipc_approval', 'cipc_approval')
        }),
        ('CAPEX Details', {
            'fields': ('cr_copy',),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('grand_total', 'request_date')
        }),
        ('Timeline', {
            'fields': ('submitted_date', 'approval_completed_date', 'pr_created_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PRApproval)
class PRApprovalAdmin(BaseModelAdmin):
    list_display = ('pr', 'approval_level', 'assigned_to', 'status', 'created_at')
    list_filter = ('status', 'approval_level', 'created_at')
    search_fields = ('pr__pr_number', 'assigned_to__username')
    readonly_fields = ('assigned_date',)


@admin.register(PRStatus)
class PRStatusAdmin(BaseModelAdmin):
    list_display = ('pr', 'from_status', 'to_status', 'changed_by', 'created_at')
    list_filter = ('from_status', 'to_status', 'created_at')
    search_fields = ('pr__pr_number',)
    readonly_fields = ('created_at',)
