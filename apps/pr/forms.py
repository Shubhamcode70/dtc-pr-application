"""
PR forms for creating and editing Purchase Requisitions.
Includes forms for PR header, line items, and vendor information.
"""

from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from django.core.exceptions import ValidationError
from decimal import Decimal
import json

from .models import PurchaseRequisition, PRItem, ApprovalChain, PRApproval
from apps.vendor.models import Vendor, VendorContact


class PRHeaderForm(forms.ModelForm):
    """Form for creating/editing PR header information."""
    
    class Meta:
        model = PurchaseRequisition
        fields = [
            'requester_name', 'department', 'purpose_of_requirement',
            'pr_type', 'plant', 'end_user_name', 'end_user_department',
            'ipc_approval_required', 'cipc_approval_required', 'pr_date'
        ]
        widgets = {
            'requester_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter requester name'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department'
            }),
            'purpose_of_requirement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the purpose of this requisition'
            }),
            'pr_type': forms.Select(attrs={'class': 'form-control'}),
            'plant': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CBE, CAPEX'
            }),
            'end_user_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'End user name'
            }),
            'end_user_department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'End user department'
            }),
            'ipc_approval_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cipc_approval_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pr_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        ipc = cleaned_data.get('ipc_approval_required')
        cipc = cleaned_data.get('cipc_approval_required')
        
        if not ipc and not cipc:
            raise ValidationError(
                "At least one approval type (IPC or CIPC) must be selected."
            )
        return cleaned_data


class PRItemForm(forms.ModelForm):
    """Form for PR line items with validation."""
    
    class Meta:
        model = PRItem
        fields = [
            'item_number', 'short_text', 'quantity', 'unit',
            'unit_price', 'total_value', 'asset_code', 'cost_center', 'gl_code'
        ]
        widgets = {
            'item_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item #',
                'readonly': True
            }),
            'short_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Qty',
                'step': '0.01'
            }),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit price',
                'step': '0.01'
            }),
            'total_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Total',
                'readonly': True
            }),
            'asset_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Asset code (for CAPEX)'
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cost center'
            }),
            'gl_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GL account'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        
        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        if unit_price and unit_price < 0:
            raise ValidationError("Unit price cannot be negative.")
        
        return cleaned_data


class PRItemFormSet(modelformset_factory(
    PRItem,
    form=PRItemForm,
    extra=4,
    can_delete=True,
    min_num=1,
    validate_min=True
)):
    """FormSet for managing multiple PR items."""
    pass


class VendorQuotationForm(forms.Form):
    """Form for adding vendor quotations to a PR."""
    
    vendor = forms.ModelChoiceField(
        queryset=Vendor.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'hx-get': '/vendor/contacts/',
            'hx-target': '#vendor-contacts'
        })
    )
    vendor_contact = forms.ModelChoiceField(
        queryset=VendorContact.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quotation_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.xlsx,.xls,.doc,.docx'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'vendor' in self.data:
            vendor_id = self.data.get('vendor')
            try:
                vendor = Vendor.objects.get(pk=vendor_id)
                self.fields['vendor_contact'].queryset = vendor.contacts.all()
            except (ValueError, Vendor.DoesNotExist):
                pass


class ApprovalForm(forms.ModelForm):
    """Form for PR approvers to approve or reject."""
    
    class Meta:
        model = PRApproval
        fields = ['approval_status', 'comments']
        widgets = {
            'approval_status': forms.Select(attrs={
                'class': 'form-control',
                'choices': [
                    ('', 'Select action'),
                    ('APPROVED', 'Approve'),
                    ('REJECTED', 'Reject'),
                ]
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add any comments or reasons for rejection'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('approval_status')
        comments = cleaned_data.get('comments')
        
        if status == 'REJECTED' and not comments:
            raise ValidationError(
                "Comments are required when rejecting a PR."
            )
        
        return cleaned_data


class PRFilterForm(forms.Form):
    """Form for filtering PR list."""
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CREATED', 'PR Created'),
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search PR ID, requester, or purpose'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    pr_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(PurchaseRequisition.PR_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class BulkActionForm(forms.Form):
    """Form for bulk actions on PRs."""
    
    ACTION_CHOICES = [
        ('', 'Select action'),
        ('export', 'Export to Excel'),
        ('mark_reviewed', 'Mark as Reviewed'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    pr_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
