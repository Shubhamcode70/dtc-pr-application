from django.contrib import admin
from django.utils.html import format_html


class BaseModelAdmin(admin.ModelAdmin):
    """Base admin class with common fields"""
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at', 'deleted_by')
    
    fieldsets = (
        ('Main Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
        ('Deletion Information', {
            'fields': ('is_deleted', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
