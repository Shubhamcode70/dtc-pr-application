"""
Forms for attachment/file handling.
"""

from django import forms
from .models import Attachment


class AttachmentUploadForm(forms.Form):
    """Form for uploading file attachments."""
    
    ATTACHMENT_TYPE_CHOICES = [
        ('QUOTATION', 'Quotation'),
        ('COMPARISON_SHEET', 'Comparison Sheet'),
        ('RFQ', 'RFQ'),
        ('SPECIFICATION', 'Specification'),
        ('APPROVAL_LETTER', 'Approval Letter'),
        ('OTHER', 'Other Document'),
    ]
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.jpg,.jpeg,.png'
        })
    )
    attachment_type = forms.ChoiceField(
        choices=ATTACHMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional description of the attachment'
        })
    )
    
    def clean_file(self):
        """Validate file."""
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size (50 MB max)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('File size must not exceed 50 MB')
            
            # Check file extension
            allowed_extensions = {
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'txt', 'csv', 'jpg', 'jpeg', 'png'
            }
            ext = file.name.rsplit('.', 1)[-1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(f'File type .{ext} not allowed')
        
        return file
