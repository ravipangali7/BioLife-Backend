from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from core.models import Order, Address, Wishlist, Product, Setting, Withdrawal, Transaction, ShippingCharge


@login_required
def account_dashboard(request):
    """User account dashboard"""
    user = request.user
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    pending_orders = Order.objects.filter(user=user, order_status='pending').count()
    
    # Get setting to check if referral system is active
    setting = Setting.objects.first() or Setting.objects.create()
    active_referal_system = setting.active_referal_system
    
    # Build referral URL if user has earn_code and referral system is active
    referral_url = None
    if user.earn_code and active_referal_system:
        referral_url = request.build_absolute_uri(f'/register/?earn_code={user.earn_code}')
    
    context = {
        'user': user,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'referral_url': referral_url,
        'setting': setting,
        'active_referal_system': active_referal_system,
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
            
        # KYC Fields
        user.citizenship_no = request.POST.get('citizenship_no', user.citizenship_no)
        if request.FILES.get('citizenship_front'):
            user.citizenship_front = request.FILES['citizenship_front']
        if request.FILES.get('citizenship_back'):
            user.citizenship_back = request.FILES['citizenship_back']
        
        # KYC status is managed in the dedicated KYC page
        
        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('website:account_profile')
    
    # Get setting for template
    setting = Setting.objects.first() or Setting.objects.create()
    
    context = {
        'user': user,
        'setting': setting,
        'active_referal_system': setting.active_referal_system,
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
    shipping_charges = ShippingCharge.objects.all().order_by('name')
    
    if request.method == 'POST':
        try:
            city_name = request.POST.get('city', '')
            shipping_charge = None
            if city_name:
                try:
                    shipping_charge = ShippingCharge.objects.get(name=city_name)
                except ShippingCharge.DoesNotExist:
                    pass
            
            Address.objects.create(
                user=request.user,
                title=request.POST.get('title', ''),
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                city=city_name,
                shipping_charge=shipping_charge,
                state=request.POST.get('state', ''),
                country=request.POST.get('country', ''),
            )
            messages.success(request, 'Address added successfully')
            return redirect('website:account_addresses')
        except Exception as e:
            messages.error(request, f'Error adding address: {str(e)}')
    
    context = {
        'action': 'Add',
        'shipping_charges': shipping_charges,
    }
    return render(request, 'site/account/address_form.html', context)


@login_required
def account_address_edit(request, address_id):
    """Edit address"""
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    
    shipping_charges = ShippingCharge.objects.all().order_by('name')
    
    if request.method == 'POST':
        try:
            city_name = request.POST.get('city', '')
            shipping_charge = None
            if city_name:
                try:
                    shipping_charge = ShippingCharge.objects.get(name=city_name)
                except ShippingCharge.DoesNotExist:
                    pass
            
            address.title = request.POST.get('title', address.title)
            address.phone = request.POST.get('phone', address.phone)
            address.address = request.POST.get('address', address.address)
            address.city = city_name
            address.shipping_charge = shipping_charge
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
        'shipping_charges': shipping_charges,
    }
    
    return render(request, 'site/account/address_form.html', context)


@login_required
def account_address_delete(request, address_id):
    """Delete address"""
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    
    if request.method == 'POST':
        # Check if address is referenced by any orders
        billing_orders_count = address.billing_orders.count()
        shipping_orders_count = address.shipping_orders.count()
        
        if billing_orders_count > 0 or shipping_orders_count > 0:
            messages.error(request, 'Cannot delete this address because it is associated with existing orders. Please contact support if you need to remove it.')
            return redirect('website:account_addresses')
        
        try:
            address.delete()
            messages.success(request, 'Address deleted successfully')
        except Exception as e:
            messages.error(request, f'Error deleting address: {str(e)}')
        
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


@login_required
def account_kyc(request):
    """Dedicated KYC verification page - allows customers to upgrade to IBO"""
    user = request.user
    
    if request.method == 'POST':
        # Store previous status for messaging
        previous_status = user.kyc_status
        was_customer = not user.is_influencer
        
        # Update KYC fields
        user.citizenship_no = request.POST.get('citizenship_no', '').strip()
        
        if request.FILES.get('citizenship_front'):
            user.citizenship_front = request.FILES['citizenship_front']
        if request.FILES.get('citizenship_back'):
            user.citizenship_back = request.FILES['citizenship_back']
        
        # Update PAN fields (optional)
        user.pan_no = request.POST.get('pan_no', '').strip() or None
        if request.FILES.get('pan_card_image'):
            user.pan_card_image = request.FILES['pan_card_image']
        
        # Validate and set status (PAN fields are optional, not required)
        if user.citizenship_no and user.citizenship_front and user.citizenship_back:
            # If all fields provided, set to pending and clear reject reason
            user.kyc_status = 'pending'
            user.kyc_reject_reason = None
            
            # If customer is submitting KYC for first time, automatically upgrade to IBO
            if was_customer:
                user.is_influencer = True
                messages.success(request, 'KYC documents submitted successfully! Your account has been upgraded to IBO (Independent Business Owner). Our admin team will review and verify your account. You will be notified once verification is complete.')
            else:
                # Existing IBO updating KYC
                if previous_status == 'approved':
                    messages.success(request, 'KYC documents updated successfully. Your account will be re-verified by our admin team. You will be notified once verification is complete.')
                elif previous_status == 'rejected':
                    messages.success(request, 'KYC documents resubmitted successfully. Our admin team will review and verify your account. You will be notified once verification is complete.')
                else:
                    messages.success(request, 'KYC documents submitted successfully. Our admin team will review and verify your account. You will be notified once verification is complete.')
            
            user.save()
        else:
            messages.warning(request, 'Please complete all KYC fields (Citizenship Number, Front, and Back) to submit for verification.')
        
        return redirect('website:account_kyc')
    
    # Get setting for template
    setting = Setting.objects.first() or Setting.objects.create()
    
    context = {
        'user': user,
        'setting': setting,
        'active_referal_system': setting.active_referal_system,
    }
    
    return render(request, 'site/account/kyc.html', context)


@login_required
def account_payment(request):
    """Payment setup page for influencers"""
    user = request.user
    
    # Only allow IBOs to access this page
    if not user.is_influencer:
        messages.error(request, 'This page is only available for IBOs.')
        return redirect('website:account_dashboard')
    
    # Check if payment setting is approved - if so, disable editing
    can_edit = user.payment_setting_status != 'approved'
    
    if request.method == 'POST' and can_edit:
        # Update payment fields
        user.esewa_number = request.POST.get('esewa_number', '').strip() or None
        user.khalti_number = request.POST.get('khalti_number', '').strip() or None
        
        if request.FILES.get('qr_code'):
            user.qr_code = request.FILES['qr_code']
        
        # Reset status to pending when payment info is updated
        user.payment_setting_status = 'pending'
        user.payment_setting_reject_reason = None
        user.save()
        messages.success(request, 'Payment information updated successfully. Your payment settings will be reviewed by admin.')
        return redirect('website:account_payment')
    elif request.method == 'POST' and not can_edit:
        messages.warning(request, 'Your payment settings have been approved. You cannot edit them.')
        return redirect('website:account_payment')
    
    context = {
        'user': user,
        'can_edit': can_edit,
    }
    
    return render(request, 'site/account/payment.html', context)


@login_required
def account_withdrawals(request):
    """Withdrawal request page for influencers"""
    user = request.user
    
    # Check if user is IBO with approved KYC
    if not user.is_influencer:
        messages.error(request, 'This page is only available for IBOs.')
        return redirect('website:account_dashboard')
    
    if user.kyc_status != 'approved':
        if user.kyc_status == 'pending':
            messages.warning(request, 'Your KYC verification is pending review. Please wait for admin approval to access withdrawal features.')
        elif user.kyc_status == 'rejected':
            reason = f": {user.kyc_reject_reason}" if user.kyc_reject_reason else ""
            messages.warning(request, f'Your KYC verification was rejected{reason}. Please update your documents and resubmit.')
        else:
            messages.warning(request, 'Please complete your KYC verification to access withdrawal features.')
        return redirect('website:account_kyc')
    
    # Get settings
    setting = Setting.objects.first() or Setting.objects.create()
    
    # Get withdrawal history
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
    
    # Handle POST request for withdrawal submission
    if request.method == 'POST':
        if not setting.is_withdrawal:
            messages.error(request, 'Withdrawals are currently disabled.')
            return redirect('website:account_withdrawals')
        
        try:
            amount = float(request.POST.get('amount', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount entered.')
            return redirect('website:account_withdrawals')
        
        # Check if payment details are set
        if not user.esewa_number and not user.khalti_number and not user.qr_code:
            messages.error(request, 'Please set up your payment details first.')
            return redirect('website:account_payment')
        
        # Validation
        if amount < float(setting.min_withdrawal):
            messages.error(request, f'Minimum withdrawal is Rs {setting.min_withdrawal}')
        elif amount > float(setting.max_withdrawal):
            messages.error(request, f'Maximum withdrawal is Rs {setting.max_withdrawal}')
        elif amount > float(user.balance):
            messages.error(request, 'Insufficient balance.')
        else:
            # Create Withdrawal
            withdrawal = Withdrawal.objects.create(
                user=user,
                amount=amount,
                status='pending',
                payment_status='pending'
            )
            
            # Deduct balance immediately (pending state)
            user.balance = float(user.balance) - amount
            user.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=user,
                amount=amount,
                transaction_type='out',
                remarks=f'Withdrawal Request (ID: {withdrawal.id})',
                status='success'  # Transaction success, withdrawal pending
            )
            
            messages.success(request, 'Withdrawal request submitted successfully.')
            return redirect('website:account_withdrawals')
    
    context = {
        'user': user,
        'setting': setting,
        'withdrawals': withdrawals,
    }
    
    return render(request, 'site/account/withdrawals.html', context)


@login_required
def account_withdrawal_detail(request, withdrawal_id):
    """Withdrawal detail view for influencers"""
    user = request.user
    
    # Check if user is IBO with approved KYC
    if not user.is_influencer:
        messages.error(request, 'This page is only available for IBOs.')
        return redirect('website:account_dashboard')
    
    if user.kyc_status != 'approved':
        messages.warning(request, 'Please complete your KYC verification to access withdrawal details.')
        return redirect('website:account_kyc')
    
    # Get withdrawal - ensure it belongs to the user
    withdrawal = get_object_or_404(Withdrawal, pk=withdrawal_id, user=user)
    
    context = {
        'user': user,
        'withdrawal': withdrawal,
    }
    
    return render(request, 'site/account/withdrawal_detail.html', context)
