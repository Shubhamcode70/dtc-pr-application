"""
Views for handling file uploads, downloads, and management.
"""

import os
import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, JsonResponse, HttpResponse
from django.views.generic import ListView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import Attachment, FileIndex
from .forms import AttachmentUploadForm
from .services import AttachmentService
from apps.pr.models import PurchaseRequisition
from apps.audit.models import AuditLog


class AttachmentListView(LoginRequiredMixin, ListView):
    """Display attachments for a PR."""
    
    model = Attachment
    template_name = 'attachments/attachment_list.html'
    context_object_name = 'attachments'
    
    def get_queryset(self):
        """Get attachments for specific PR."""
        pr_id = self.kwargs['pr_id']
        return Attachment.objects.filter(
            purchase_requisition__pr_id=pr_id,
            is_deleted=False
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pr = get_object_or_404(
            PurchaseRequisition,
            pr_id=self.kwargs['pr_id']
        )
        context['pr'] = pr
        context['upload_form'] = AttachmentUploadForm()
        return context


class AttachmentUploadView(LoginRequiredMixin, CreateView):
    """Handle file uploads."""
    
    model = Attachment
    form_class = AttachmentUploadForm
    template_name = 'attachments/attachment_upload.html'
    
    def post(self, request, *args, **kwargs):
        """Handle file upload via AJAX or form."""
        pr_id = kwargs.get('pr_id')
        pr = get_object_or_404(PurchaseRequisition, pr_id=pr_id)
        
        form = AttachmentUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            file = request.FILES.get('file')
            
            # Validate file
            service = AttachmentService()
            is_valid, error_msg = service.validate_file(file)
            
            if not is_valid:
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=400)
            
            # Save attachment
            try:
                attachment = Attachment.objects.create(
                    purchase_requisition=pr,
                    uploaded_by=request.user,
                    file=file,
                    attachment_type=form.cleaned_data.get('attachment_type', 'OTHER'),
                    description=form.cleaned_data.get('description', ''),
                )
                
                # Create file index for faster retrieval
                FileIndex.objects.create(
                    attachment=attachment,
                    file_path=str(attachment.file),
                    file_size=attachment.file.size,
                    mime_type=mimetypes.guess_type(attachment.file.name)[0],
                    stored_date=timezone.now()
                )
                
                # Log action
                AuditLog.objects.create(
                    user=request.user,
                    action='FILE_UPLOADED',
                    object_type='Attachment',
                    object_id=attachment.id,
                    description=f'File {attachment.file.name} uploaded to PR {pr.pr_id}'
                )
                
                messages.success(request, 'File uploaded successfully.')
                
                # Return JSON for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'attachment_id': attachment.id,
                        'file_name': attachment.file.name,
                        'file_size': attachment.file.size,
                    })
                
                return redirect('attachments:attachment-list', pr_id=pr_id)
            
            except Exception as e:
                messages.error(request, f'Error uploading file: {str(e)}')
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        
        return JsonResponse({
            'success': False,
            'error': 'Invalid form submission'
        }, status=400)


@require_GET
def download_attachment(request, attachment_id):
    """Download a file attachment."""
    attachment = get_object_or_404(Attachment, id=attachment_id)
    
    # Check permission - user must have access to PR
    pr = attachment.purchase_requisition
    user = request.user
    
    # Check if user is creator, approver, or admin
    can_access = (
        pr.created_by == user or
        user.role.name == 'Admin' or
        pr.approvals.filter(approver=user).exists()
    )
    
    if not can_access:
        messages.error(request, 'You do not have permission to download this file.')
        return redirect('pr:pr-list')
    
    # Log download
    AuditLog.objects.create(
        user=user,
        action='FILE_DOWNLOADED',
        object_type='Attachment',
        object_id=attachment.id,
        description=f'File {attachment.file.name} downloaded'
    )
    
    # Return file
    file_path = attachment.file.path if hasattr(attachment.file, 'path') else None
    
    if file_path and os.path.exists(file_path):
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=attachment.file.name
        )
    
    # Fallback to file content from storage
    file_content = attachment.file.read()
    response = HttpResponse(file_content)
    response['Content-Type'] = mimetypes.guess_type(attachment.file.name)[0] or 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{attachment.file.name}"'
    
    return response


class AttachmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete (soft delete) an attachment."""
    
    model = Attachment
    template_name = 'attachments/attachment_confirm_delete.html'
    
    def test_func(self):
        """Only uploader or admin can delete."""
        attachment = self.get_object()
        return (
            attachment.uploaded_by == self.request.user or
            self.request.user.role.name == 'Admin'
        )
    
    def delete(self, request, *args, **kwargs):
        """Soft delete attachment."""
        attachment = self.get_object()
        pr_id = attachment.purchase_requisition.pr_id
        
        attachment.is_deleted = True
        attachment.save()
        
        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='FILE_DELETED',
            object_type='Attachment',
            object_id=attachment.id,
            description=f'File {attachment.file.name} deleted'
        )
        
        messages.success(request, 'File deleted successfully.')
        return redirect('attachments:attachment-list', pr_id=pr_id)
    
    def get_success_url(self):
        return reverse_lazy(
            'attachments:attachment-list',
            kwargs={'pr_id': self.object.purchase_requisition.pr_id}
        )


class AttachmentService:
    """Service class for file management operations."""
    
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'txt', 'csv', 'jpg', 'jpeg', 'png', 'gif'
    }
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    def validate_file(self, file):
        """
        Validate uploaded file.
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not file:
            return False, "No file provided"
        
        # Check file size
        if file.size > self.MAX_FILE_SIZE:
            return False, f"File size exceeds {self.MAX_FILE_SIZE / 1024 / 1024}MB limit"
        
        # Check file extension
        ext = file.name.rsplit('.', 1)[-1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"File type .{ext} not allowed"
        
        return True, None
    
    def get_file_metadata(self, file) -> dict:
        """Extract file metadata."""
        return {
            'name': file.name,
            'size': file.size,
            'mime_type': mimetypes.guess_type(file.name)[0],
            'uploaded_at': timezone.now(),
        }
    
    def organize_file_path(self, pr, file) -> str:
        """
        Organize file path with year/month/pr_id structure.
        
        Returns:
            Organized file path
        """
        now = timezone.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        pr_id = pr.pr_id
        
        return f'pr_attachments/{year}/{month}/{pr_id}/{file.name}'
