"""Vendor URLs"""
from django.urls import path
from . import views

app_name = 'vendor'

urlpatterns = [
    path('', views.VendorListView.as_view(), name='vendor-list'),
    path('<int:pk>/', views.VendorDetailView.as_view(), name='vendor-detail'),
    path('create/', views.VendorCreateView.as_view(), name='vendor-create'),
    path('<int:pk>/edit/', views.VendorUpdateView.as_view(), name='vendor-edit'),
    path('<int:pk>/delete/', views.VendorDeleteView.as_view(), name='vendor-delete'),
    path('api/contacts/', views.vendor_contacts_api, name='contacts-api'),
    path('api/search/', views.vendor_search_api, name='search-api'),
    path('<int:vendor_pk>/quotations/', views.VendorQuotationListView.as_view(), name='quotations'),
]
