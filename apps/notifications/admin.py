from django.contrib import admin
from apps.notifications.models import NotificationTemplate, Notification, UserNotificationPreference
from apps.core.admin import BaseModelAdmin


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(BaseModelAdmin):
    list_display = ('display_name', 'event_type', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('display_name', 'event_type')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'status', 'created_at')
    list_filter = ('status', 'notification_type', 'created_at')
    search_fields = ('user__username', 'subject')
    readonly_fields = ('created_at', 'sent_date')


@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(BaseModelAdmin):
    list_display = ('user', 'email_on_pr_submitted', 'email_on_pr_approved')
    list_filter = ('email_on_pr_submitted', 'email_digest')
    search_fields = ('user__username',)
