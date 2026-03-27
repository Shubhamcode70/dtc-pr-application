"""
URL Configuration for DTC PR Application
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls', namespace='auth')),
    path('api/pr/', include('apps.pr.urls', namespace='pr')),
    path('api/vendor/', include('apps.vendor.urls', namespace='vendor')),
    path('api/attachments/', include('apps.attachments.urls', namespace='attachments')),
    path('api/audit/', include('apps.audit.urls', namespace='audit')),
    path('api/notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('api/dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
