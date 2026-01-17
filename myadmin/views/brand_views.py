from django.shortcuts import render, get_object_or_404, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Brand
from django.forms import modelform_factory
from django import forms


@superuser_required
def brand_list(request):
    """List all brands"""
    brands = Brand.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        brands = brands.filter(name__icontains=search_query)
    
    paginator = Paginator(brands, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'brands': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'admin/brands/list.html', context)


@superuser_required
def brand_detail(request, pk):
    """Brand detail view"""
    brand = get_object_or_404(Brand, pk=pk)
    products = brand.products.all()[:10]
    
    context = {
        'brand': brand,
        'products': products,
    }
    
    return render(request, 'admin/brands/detail.html', context)


@superuser_required
def brand_create(request):
    """Create new brand"""
    BrandForm = modelform_factory(
        Brand,
        fields=['name', 'logo'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            brand = form.save()
            messages.success(request, f'Brand "{brand.name}" created successfully.')
            return redirect('myadmin:brand_detail', pk=brand.pk)
    else:
        form = BrandForm()
    
    return render(request, 'admin/brands/form.html', {'form': form})


@superuser_required
def brand_edit(request, pk):
    """Edit brand"""
    brand = get_object_or_404(Brand, pk=pk)
    
    BrandForm = modelform_factory(
        Brand,
        fields=['name', 'logo'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            brand = form.save()
            messages.success(request, f'Brand "{brand.name}" updated successfully.')
            return redirect('myadmin:brand_detail', pk=brand.pk)
    else:
        form = BrandForm(instance=brand)
    
    return render(request, 'admin/brands/form.html', {'form': form, 'brand': brand})


@superuser_required
def brand_delete(request, pk):
    """Delete brand"""
    brand = get_object_or_404(Brand, pk=pk)
    
    if request.method == 'POST':
        brand_name = brand.name
        brand.delete()
        messages.success(request, f'Brand "{brand_name}" deleted successfully.')
        return redirect('myadmin:brand_list')
    
    return render(request, 'admin/brands/delete.html', {'brand': brand})

