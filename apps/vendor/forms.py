"""
Forms for vendor management.
"""

from django import forms
from django.forms import inlineformset_factory
from .models import Vendor, VendorContact


class VendorForm(forms.ModelForm):
    """Form for creating/editing vendors."""
    
    class Meta:
        model = Vendor
        fields = ['name', 'email', 'phone', 'location', 'gstin', 'pan', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vendor name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City/Location'
            }),
            'gstin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'GST ID'
            }),
            'pan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PAN'
            }),
            'status': forms.Select(attrs={'class': 'form-control'})
        }
    
    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists (excluding current instance)
            qs = Vendor.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('This email is already registered.')
        return email


class VendorContactForm(forms.ModelForm):
    """Form for vendor contacts."""
    
    class Meta:
        model = VendorContact
        fields = ['name', 'email', 'phone', 'location', 'designation']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job title'
            }),
        }


VendorContactFormSet = inlineformset_factory(
    Vendor,
    VendorContact,
    form=VendorContactForm,
    extra=2,
    can_delete=True
)


class VendorFilterForm(forms.Form):
    """Form for filtering vendors."""
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('BLACKLISTED', 'Blacklisted'),
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or location'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
