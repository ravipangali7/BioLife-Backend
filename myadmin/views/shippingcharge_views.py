from django.shortcuts import render, get_object_or_404, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import ShippingCharge
from django.forms import modelform_factory
from django import forms


@superuser_required
def shippingcharge_list(request):
    """List all shipping charges"""
    shipping_charges = ShippingCharge.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        shipping_charges = shipping_charges.filter(
            Q(name__icontains=search_query)
        )
    
    paginator = Paginator(shipping_charges, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'shipping_charges': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'admin/shippingcharges/list.html', context)


@superuser_required
def shippingcharge_detail(request, pk):
    """Shipping charge detail view"""
    shipping_charge = get_object_or_404(ShippingCharge, pk=pk)
    addresses = shipping_charge.addresses.all()[:10]
    orders = shipping_charge.orders.all()[:10]
    
    context = {
        'shipping_charge': shipping_charge,
        'addresses': addresses,
        'orders': orders,
        'addresses_count': shipping_charge.addresses.count(),
        'orders_count': shipping_charge.orders.count(),
    }
    
    return render(request, 'admin/shippingcharges/detail.html', context)


@superuser_required
def shippingcharge_create(request):
    """Create new shipping charge"""
    ShippingChargeForm = modelform_factory(
        ShippingCharge,
        fields=['name', 'charge'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city name'}),
            'charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
    )
    
    if request.method == 'POST':
        form = ShippingChargeForm(request.POST)
        if form.is_valid():
            shipping_charge = form.save()
            messages.success(request, f'Shipping charge for "{shipping_charge.name}" created successfully.')
            return redirect('myadmin:shippingcharge_detail', pk=shipping_charge.pk)
    else:
        form = ShippingChargeForm()
    
    return render(request, 'admin/shippingcharges/form.html', {'form': form})


@superuser_required
def shippingcharge_edit(request, pk):
    """Edit shipping charge"""
    shipping_charge = get_object_or_404(ShippingCharge, pk=pk)
    
    ShippingChargeForm = modelform_factory(
        ShippingCharge,
        fields=['name', 'charge'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city name'}),
            'charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
    )
    
    if request.method == 'POST':
        form = ShippingChargeForm(request.POST, instance=shipping_charge)
        if form.is_valid():
            shipping_charge = form.save()
            messages.success(request, f'Shipping charge for "{shipping_charge.name}" updated successfully.')
            return redirect('myadmin:shippingcharge_detail', pk=shipping_charge.pk)
    else:
        form = ShippingChargeForm(instance=shipping_charge)
    
    return render(request, 'admin/shippingcharges/form.html', {'form': form, 'shipping_charge': shipping_charge})


@superuser_required
def shippingcharge_delete(request, pk):
    """Delete shipping charge"""
    shipping_charge = get_object_or_404(ShippingCharge, pk=pk)
    
    # Get counts for warning message
    addresses_count = shipping_charge.addresses.count()
    orders_count = shipping_charge.orders.count()
    
    if request.method == 'POST':
        shipping_charge_name = shipping_charge.name
        shipping_charge.delete()
        messages.success(request, f'Shipping charge for "{shipping_charge_name}" deleted successfully.')
        return redirect('myadmin:shippingcharge_list')
    
    context = {
        'shipping_charge': shipping_charge,
        'addresses_count': addresses_count,
        'orders_count': orders_count,
    }
    return render(request, 'admin/shippingcharges/delete.html', context)
