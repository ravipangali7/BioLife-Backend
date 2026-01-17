from django.shortcuts import render, get_object_or_404, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.db import transaction
from core.models import Product, Setting
from django import forms
from django.forms import modelform_factory


@superuser_required
def inventory_dashboard(request):
    """Inventory overview dashboard"""
    # Get global low stock threshold from settings
    setting = Setting.objects.first()
    low_stock_threshold = setting.low_stock_threshold if setting else 10
    
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    
    # Stock statistics
    total_stock_value = 0
    products_with_stock = Product.objects.filter(stock__gt=0).count()
    out_of_stock = Product.objects.filter(stock=0, is_active=True).count()
    low_stock_count = Product.objects.filter(
        stock__lte=low_stock_threshold,
        stock__gt=0,
        is_active=True
    ).count()
    
    # Calculate total stock value
    for product in Product.objects.filter(is_active=True):
        total_stock_value += float(product.regular_price) * product.stock
    
    # Low stock products (real-time calculation)
    low_stock_products = Product.objects.filter(
        stock__gt=0,
        stock__lte=low_stock_threshold,
        is_active=True
    ).order_by('stock')[:10]
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'products_with_stock': products_with_stock,
        'out_of_stock': out_of_stock,
        'low_stock_count': low_stock_count,
        'total_stock_value': total_stock_value,
        'low_stock_products': low_stock_products,
        'low_stock_threshold': low_stock_threshold,
    }
    
    return render(request, 'admin/inventory/dashboard.html', context)


@superuser_required
def low_stock_list(request):
    """List products with low stock"""
    # Get global low stock threshold from settings
    setting = Setting.objects.first()
    low_stock_threshold = setting.low_stock_threshold if setting else 10
    
    products = Product.objects.filter(
        stock__lte=low_stock_threshold,
        is_active=True
    ).order_by('stock', 'name')
    
    # Filter by stock status
    status_filter = request.GET.get('status')
    if status_filter == 'out_of_stock':
        products = products.filter(stock=0)
    elif status_filter == 'low_stock':
        products = products.filter(stock__gt=0, stock__lte=low_stock_threshold)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'low_stock_threshold': low_stock_threshold,
    }
    
    return render(request, 'admin/inventory/low_stock.html', context)


@superuser_required
def bulk_stock_update(request):
    """Bulk stock operations (CSV import/export)"""
    if request.method == 'POST' and 'export' in request.POST:
        # Export products with stock to CSV
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stock_export.csv"'
        
        # Get global low stock threshold from settings
        setting = Setting.objects.first()
        low_stock_threshold = setting.low_stock_threshold if setting else 10
        
        writer = csv.writer(response)
        writer.writerow(['SKU', 'Product Name', 'Current Stock', 'Low Stock Threshold', 'Price'])
        
        products = Product.objects.filter(is_active=True).order_by('name')
        for product in products:
            writer.writerow([
                product.sku,
                product.name,
                product.stock,
                low_stock_threshold,
                product.regular_price
            ])
        
        return response
    
    context = {}
    return render(request, 'admin/inventory/bulk_update.html', context)
