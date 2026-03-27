"""PR URLs"""
from django.urls import path
from . import views

app_name = 'pr'

urlpatterns = [
    path('', views.PRListView.as_view(), name='pr-list'),
    path('create/', views.PRCreateView.as_view(), name='pr-create'),
    path('<str:pr_id>/', views.PRDetailView.as_view(), name='pr-detail'),
    path('<str:pr_id>/edit/', views.PRUpdateView.as_view(), name='pr-edit'),
    path('<str:pr_id>/submit/', views.PRSubmitView.as_view(), name='pr-submit'),
    path('<str:pr_id>/approve/', views.approve_pr, name='pr-approve'),
    path('<str:pr_id>/export/', views.PRExportView.as_view(), name='pr-export'),
    path('pending-approvals/', views.MyPendingApprovalsView.as_view(), name='pending-approvals'),
]
