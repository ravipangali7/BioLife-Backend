from django.shortcuts import render, get_object_or_404, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Unit
from django.forms import modelform_factory
from django import forms


@superuser_required
def unit_list(request):
    """List all units"""
    units = Unit.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        units = units.filter(
            Q(title__icontains=search_query) |
            Q(symbol__icontains=search_query)
        )
    
    paginator = Paginator(units, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'units': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'admin/units/list.html', context)


@superuser_required
def unit_detail(request, pk):
    """Unit detail view"""
    unit = get_object_or_404(Unit, pk=pk)
    products = unit.products.all()[:10]
    
    context = {
        'unit': unit,
        'products': products,
    }
    
    return render(request, 'admin/units/detail.html', context)


@superuser_required
def unit_create(request):
    """Create new unit"""
    UnitForm = modelform_factory(
        Unit,
        fields=['title', 'symbol'],
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f'Unit "{unit.title}" created successfully.')
            return redirect('myadmin:unit_detail', pk=unit.pk)
    else:
        form = UnitForm()
    
    return render(request, 'admin/units/form.html', {'form': form})


@superuser_required
def unit_edit(request, pk):
    """Edit unit"""
    unit = get_object_or_404(Unit, pk=pk)
    
    UnitForm = modelform_factory(
        Unit,
        fields=['title', 'symbol'],
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f'Unit "{unit.title}" updated successfully.')
            return redirect('myadmin:unit_detail', pk=unit.pk)
    else:
        form = UnitForm(instance=unit)
    
    return render(request, 'admin/units/form.html', {'form': form, 'unit': unit})


@superuser_required
def unit_delete(request, pk):
    """Delete unit"""
    unit = get_object_or_404(Unit, pk=pk)
    
    if request.method == 'POST':
        unit_title = unit.title
        unit.delete()
        messages.success(request, f'Unit "{unit_title}" deleted successfully.')
        return redirect('myadmin:unit_list')
    
    return render(request, 'admin/units/delete.html', {'unit': unit})

