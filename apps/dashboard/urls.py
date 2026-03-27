"""Dashboard URLs"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('my-prs/', views.MyPRsDashboardView.as_view(), name='my-prs'),
    path('approvals-queue/', views.ApprovalsQueueView.as_view(), name='approvals-queue'),
    path('audit/', views.AuditDashboardView.as_view(), name='audit'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
]
