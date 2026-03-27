"""Vendor Management Models"""

from django.db import models
from apps.core.models import AuditableModel


class Vendor(AuditableModel):
    """Vendor Master"""
    
    name = models.CharField(max_length=255, db_index=True)
    vendor_code = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='India')
    
    # Banking details
    bank_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    rating = models.IntegerField(default=0, help_text="0-5 star rating")
    
    class Meta:
        app_label = 'vendor'
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.vendor_code})"


class VendorContact(AuditableModel):
    """Vendor Contact Persons"""
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'vendor'
        verbose_name = 'Vendor Contact'
        verbose_name_plural = 'Vendor Contacts'
    
    def __str__(self):
        return f"{self.name} ({self.vendor.name})"


class VendorQuotation(AuditableModel):
    """Quotations from Vendors"""
    
    pr = models.ForeignKey('pr.PurchaseRequisition', on_delete=models.CASCADE, related_name='quotations')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='quotations')
    quotation_number = models.CharField(max_length=100)
    quotation_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    delivery_days = models.IntegerField(blank=True, null=True)
    validity_days = models.IntegerField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True)
    
    class Meta:
        app_label = 'vendor'
        verbose_name = 'Vendor Quotation'
        verbose_name_plural = 'Vendor Quotations'
    
    def __str__(self):
        return f"{self.quotation_number} - {self.vendor.name}"
