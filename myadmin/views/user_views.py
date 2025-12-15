from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import User, Address
from django.forms import modelform_factory
from django import forms


@login_required
def user_list(request):
    """List all users"""
    users = User.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    influencer_filter = request.GET.get('influencer')
    if influencer_filter == 'yes':
        users = users.filter(is_influencer=True)
    elif influencer_filter == 'no':
        users = users.filter(is_influencer=False)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'influencer_filter': influencer_filter,
    }
    
    return render(request, 'admin/users/list.html', context)


@login_required
def user_detail(request, pk):
    """User detail view"""
    user = get_object_or_404(User, pk=pk)
    addresses = Address.objects.filter(user=user)
    orders = user.orders.all()[:10]
    reviews = user.reviews.all()[:10]
    
    context = {
        'user': user,
        'addresses': addresses,
        'orders': orders,
        'reviews': reviews,
    }
    
    return render(request, 'admin/users/detail.html', context)


@login_required
def user_edit(request, pk):
    """Edit user"""
    user = get_object_or_404(User, pk=pk)
    
    UserForm = modelform_factory(
        User,
        fields=['name', 'email', 'phone', 'date_of_birth', 'address', 'is_influencer',
                'tiktok_link', 'facebook_link', 'instagram_link', 'youtube_link', 'image', 'points', 'is_active'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_influencer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tiktok_link': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook_link': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_link': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube_link': forms.URLInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.email}" updated successfully.')
            return redirect('myadmin:user_detail', pk=user.pk)
    else:
        form = UserForm(instance=user)
    
    return render(request, 'admin/users/form.html', {'form': form, 'user': user})


@login_required
def address_list(request, user_pk):
    """List user addresses"""
    user = get_object_or_404(User, pk=user_pk)
    addresses = Address.objects.filter(user=user)
    
    context = {
        'user': user,
        'addresses': addresses,
    }
    
    return render(request, 'admin/users/address_list.html', context)


@login_required
def address_detail(request, pk):
    """Address detail view"""
    address = get_object_or_404(Address.objects.select_related('user'), pk=pk)
    
    context = {
        'address': address,
    }
    
    return render(request, 'admin/users/address_detail.html', context)


@login_required
def address_create(request, user_pk):
    """Create new address"""
    user = get_object_or_404(User, pk=user_pk)
    
    AddressForm = modelform_factory(
        Address,
        fields=['title', 'phone', 'address', 'city', 'state', 'country'],
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
            messages.success(request, f'Address "{address.title}" created successfully.')
            return redirect('myadmin:address_detail', pk=address.pk)
    else:
        form = AddressForm()
    
    return render(request, 'admin/users/address_form.html', {'form': form, 'user': user})


@login_required
def address_edit(request, pk):
    """Edit address"""
    address = get_object_or_404(Address, pk=pk)
    
    AddressForm = modelform_factory(
        Address,
        fields=['title', 'phone', 'address', 'city', 'state', 'country'],
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save()
            messages.success(request, f'Address "{address.title}" updated successfully.')
            return redirect('myadmin:address_detail', pk=address.pk)
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'admin/users/address_form.html', {'form': form, 'address': address})


@login_required
def address_delete(request, pk):
    """Delete address"""
    address = get_object_or_404(Address, pk=pk)
    
    if request.method == 'POST':
        address_title = address.title
        user_pk = address.user.pk
        address.delete()
        messages.success(request, f'Address "{address_title}" deleted successfully.')
        return redirect('myadmin:address_list', user_pk=user_pk)
    
    return render(request, 'admin/users/address_delete.html', {'address': address})

