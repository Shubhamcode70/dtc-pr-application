from django.contrib import admin
from apps.vendor.models import Vendor, VendorContact, VendorQuotation
from apps.core.admin import BaseModelAdmin


@admin.register(Vendor)
class VendorAdmin(BaseModelAdmin):
    list_display = ('name', 'vendor_code', 'email', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'vendor_code', 'email')


@admin.register(VendorContact)
class VendorContactAdmin(BaseModelAdmin):
    list_display = ('name', 'vendor', 'email', 'is_primary')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('name', 'email', 'vendor__name')


@admin.register(VendorQuotation)
class VendorQuotationAdmin(BaseModelAdmin):
    list_display = ('quotation_number', 'vendor', 'amount', 'quotation_date')
    list_filter = ('quotation_date', 'currency')
    search_fields = ('quotation_number', 'vendor__name')
