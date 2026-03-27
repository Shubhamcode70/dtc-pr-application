"""Attachments URLs"""
from django.urls import path
from . import views

app_name = 'attachments'

urlpatterns = [
    path('pr/<str:pr_id>/', views.AttachmentListView.as_view(), name='attachment-list'),
    path('upload/<str:pr_id>/', views.AttachmentUploadView.as_view(), name='attachment-upload'),
    path('download/<int:attachment_id>/', views.download_attachment, name='attachment-download'),
    path('delete/<int:pk>/', views.AttachmentDeleteView.as_view(), name='attachment-delete'),
]
