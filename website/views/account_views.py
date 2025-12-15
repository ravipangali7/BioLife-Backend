from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from core.models import Order, Address, Wishlist, Product


@login_required
def account_dashboard(request):
    """User account dashboard"""
    user = request.user
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    pending_orders = Order.objects.filter(user=user, order_status='pending').count()
    
    context = {
        'user': user,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
    }
    
    return render(request, 'site/account/dashboard.html', context)


@login_required
def account_profile(request):
    """Edit user profile"""
    user = request.user
    
    if request.method == 'POST':
        user.name = request.POST.get('name', user.name)
        user.phone = request.POST.get('phone', user.phone)
        user.date_of_birth = request.POST.get('date_of_birth') or None
        user.address = request.POST.get('address', user.address)
        
        if request.FILES.get('image'):
            user.image = request.FILES['image']
        
        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('website:account_profile')
    
    context = {
        'user': user,
    }
    
    return render(request, 'site/account/profile.html', context)


@login_required
def account_orders(request):
    """Order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'site/account/orders.html', context)


@login_required
def account_order_detail(request, order_id):
    """Order detail view"""
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'site/account/order_detail.html', context)


@login_required
def account_addresses(request):
    """Address management"""
    addresses = Address.objects.filter(user=request.user)
    
    context = {
        'addresses': addresses,
    }
    
    return render(request, 'site/account/addresses.html', context)


@login_required
def account_address_create(request):
    """Create new address"""
    if request.method == 'POST':
        try:
            Address.objects.create(
                user=request.user,
                title=request.POST.get('title', ''),
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                city=request.POST.get('city', ''),
                state=request.POST.get('state', ''),
                country=request.POST.get('country', ''),
            )
            messages.success(request, 'Address added successfully')
            return redirect('website:account_addresses')
        except Exception as e:
            messages.error(request, f'Error adding address: {str(e)}')
    
    return render(request, 'site/account/address_form.html', {'action': 'Add'})


@login_required
def account_address_edit(request, address_id):
    """Edit address"""
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    
    if request.method == 'POST':
        try:
            address.title = request.POST.get('title', address.title)
            address.phone = request.POST.get('phone', address.phone)
            address.address = request.POST.get('address', address.address)
            address.city = request.POST.get('city', address.city)
            address.state = request.POST.get('state', address.state)
            address.country = request.POST.get('country', address.country)
            address.save()
            messages.success(request, 'Address updated successfully')
            return redirect('website:account_addresses')
        except Exception as e:
            messages.error(request, f'Error updating address: {str(e)}')
    
    context = {
        'address': address,
        'action': 'Edit',
    }
    
    return render(request, 'site/account/address_form.html', context)


@login_required
def account_address_delete(request, address_id):
    """Delete address"""
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully')
        return redirect('website:account_addresses')
    
    context = {
        'address': address,
    }
    
    return render(request, 'site/account/address_delete.html', context)


@login_required
def wishlist_view(request):
    """Display user's wishlist"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    
    return render(request, 'site/account/wishlist.html', context)


@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            messages.success(request, 'Product added to wishlist')
        else:
            messages.info(request, 'Product is already in your wishlist')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Added to wishlist' if created else 'Already in wishlist',
                'wishlist_count': Wishlist.objects.filter(user=request.user).count()
            })
    
    return redirect('website:product_detail', pk=product_id)


@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    if request.method == 'POST':
        wishlist_item = get_object_or_404(
            Wishlist,
            user=request.user,
            product_id=product_id
        )
        wishlist_item.delete()
        messages.success(request, 'Product removed from wishlist')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Removed from wishlist',
                'wishlist_count': Wishlist.objects.filter(user=request.user).count()
            })
    
    return redirect('website:wishlist')
