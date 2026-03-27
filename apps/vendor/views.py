"""
Vendor management views for managing vendor information and contacts.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET

from .models import Vendor, VendorContact
from .forms import VendorForm, VendorContactFormSet


class VendorListView(LoginRequiredMixin, ListView):
    """Display list of all vendors."""
    
    model = Vendor
    template_name = 'vendor/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 20
    
    def get_queryset(self):
        """Search vendors by name or email."""
        queryset = Vendor.objects.prefetch_related('contacts').all()
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(location__icontains=search)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class VendorDetailView(LoginRequiredMixin, DetailView):
    """Display detailed vendor information."""
    
    model = Vendor
    template_name = 'vendor/vendor_detail.html'
    context_object_name = 'vendor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.get_object()
        
        context['contacts'] = vendor.contacts.all()
        context['total_quotations'] = vendor.quotations.count()
        
        return context


class VendorCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new vendor."""
    
    model = Vendor
    form_class = VendorForm
    template_name = 'vendor/vendor_form.html'
    success_url = reverse_lazy('vendor:vendor-list')
    
    def test_func(self):
        """Only admin and staff can create vendors."""
        return self.request.user.role.name in ['Admin', 'Manager']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['contact_formset'] = VendorContactFormSet(self.request.POST)
        else:
            context['contact_formset'] = VendorContactFormSet()
        
        return context
    
    def form_valid(self, form):
        """Create vendor with contacts."""
        context = self.get_context_data()
        contact_formset = context['contact_formset']
        
        if contact_formset.is_valid():
            vendor = form.save()
            
            for contact_form in contact_formset:
                if contact_form.cleaned_data:
                    contact = contact_form.save(commit=False)
                    contact.vendor = vendor
                    contact.save()
            
            messages.success(
                self.request,
                f'Vendor {vendor.name} created successfully.'
            )
            return redirect('vendor:vendor-detail', pk=vendor.pk)
        else:
            return self.form_invalid(form)


class VendorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit vendor information."""
    
    model = Vendor
    form_class = VendorForm
    template_name = 'vendor/vendor_form.html'
    
    def test_func(self):
        """Only admin and staff can edit vendors."""
        return self.request.user.role.name in ['Admin', 'Manager']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['contact_formset'] = VendorContactFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['contact_formset'] = VendorContactFormSet(instance=self.object)
        
        return context
    
    def form_valid(self, form):
        """Update vendor and contacts."""
        context = self.get_context_data()
        contact_formset = context['contact_formset']
        
        if contact_formset.is_valid():
            vendor = form.save()
            contact_formset.instance = vendor
            contact_formset.save()
            
            messages.success(
                self.request,
                f'Vendor {vendor.name} updated successfully.'
            )
            return redirect('vendor:vendor-detail', pk=vendor.pk)
        else:
            return self.form_invalid(form)


class VendorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a vendor (soft delete)."""
    
    model = Vendor
    template_name = 'vendor/vendor_confirm_delete.html'
    success_url = reverse_lazy('vendor:vendor-list')
    
    def test_func(self):
        """Only admin can delete vendors."""
        return self.request.user.role.name == 'Admin'
    
    def delete(self, request, *args, **kwargs):
        """Soft delete vendor."""
        vendor = self.get_object()
        vendor.is_deleted = True
        vendor.save()
        
        messages.success(request, f'Vendor {vendor.name} deleted.')
        return redirect(self.success_url)


@require_GET
def vendor_contacts_api(request):
    """API endpoint to get contacts for a vendor (for AJAX requests)."""
    vendor_id = request.GET.get('vendor_id')
    
    if not vendor_id:
        return JsonResponse({'error': 'Vendor ID required'}, status=400)
    
    try:
        vendor = Vendor.objects.get(pk=vendor_id)
        contacts = vendor.contacts.filter(is_deleted=False).values(
            'id', 'name', 'email', 'location'
        )
        
        return JsonResponse({
            'success': True,
            'contacts': list(contacts)
        })
    except Vendor.DoesNotExist:
        return JsonResponse({'error': 'Vendor not found'}, status=404)


@require_GET
def vendor_search_api(request):
    """API endpoint for vendor search (for autocomplete)."""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    vendors = Vendor.objects.filter(
        Q(name__icontains=query) |
        Q(email__icontains=query),
        is_deleted=False
    ).values('id', 'name', 'email')[:10]
    
    return JsonResponse({
        'results': list(vendors)
    })


class VendorQuotationListView(LoginRequiredMixin, ListView):
    """Display quotations for a vendor."""
    
    model = VendorContact
    template_name = 'vendor/quotation_list.html'
    context_object_name = 'quotations'
    paginate_by = 20
    
    def get_vendor(self):
        """Get vendor from URL."""
        return get_object_or_404(Vendor, pk=self.kwargs['vendor_pk'])
    
    def get_queryset(self):
        """Get quotations for specific vendor."""
        vendor = self.get_vendor()
        return vendor.quotations.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.get_vendor()
        return context
