from django.contrib import admin
from apps.attachments.models import AttachmentType, Attachment, FileIndex, AccessLog
from apps.core.admin import BaseModelAdmin


@admin.register(AttachmentType)
class AttachmentTypeAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'type_key', 'is_required')
    search_fields = ('display_name', 'type_key')


@admin.register(Attachment)
class AttachmentAdmin(BaseModelAdmin):
    list_display = ('original_filename', 'pr', 'attachment_type', 'file_size', 'uploaded_by')
    list_filter = ('attachment_type', 'upload_date', 'is_scanned')
    search_fields = ('original_filename', 'file_hash')
    readonly_fields = ('file_hash', 'upload_date')


@admin.register(FileIndex)
class FileIndexAdmin(BaseModelAdmin):
    list_display = ('file_path', 'access_count', 'last_accessed', 'is_archived')
    list_filter = ('is_archived', 'created_at')
    search_fields = ('file_path',)


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'attachment', 'created_at')
    list_filter = ('action', 'success', 'created_at')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'action', 'attachment', 'ip_address')
