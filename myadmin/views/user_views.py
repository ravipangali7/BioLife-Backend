from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db import transaction
from decimal import Decimal
from core.models import User, Address, Transaction, Withdrawal
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
    
    # Wallet and transaction data
    recent_transactions = user.transactions.all()[:20]
    recent_withdrawals = user.withdrawals.all()[:20]
    
    # Transaction statistics
    transactions_all = user.transactions.all()
    transaction_stats = {
        'total_credit': transactions_all.filter(transaction_type='in', status='success').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00'),
        'total_debit': transactions_all.filter(transaction_type='out', status='success').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00'),
        'count': transactions_all.count(),
    }
    
    # Withdrawal statistics
    withdrawals_all = user.withdrawals.all()
    withdrawal_stats = {
        'pending': withdrawals_all.filter(status='pending').count(),
        'approved': withdrawals_all.filter(status='approved').count(),
        'rejected': withdrawals_all.filter(status='rejected').count(),
        'total_amount': withdrawals_all.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00'),
    }
    
    context = {
        'user': user,
        'addresses': addresses,
        'orders': orders,
        'reviews': reviews,
        'user_balance': user.balance,
        'recent_transactions': recent_transactions,
        'recent_withdrawals': recent_withdrawals,
        'transaction_stats': transaction_stats,
        'withdrawal_stats': withdrawal_stats,
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


# --- WALLET & TRANSACTION MANAGEMENT ---

@login_required
def user_balance_adjust(request, pk):
    """Manually adjust user balance"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            transaction_type = request.POST.get('transaction_type', 'in')
            remarks = request.POST.get('remarks', 'Manual balance adjustment')
            
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero.')
                return redirect('myadmin:user_detail', pk=pk)
            
            # Check if debit would result in negative balance
            if transaction_type == 'out' and user.balance < amount:
                messages.error(request, f'Insufficient balance. Current balance: Rs {user.balance}')
                return redirect('myadmin:user_detail', pk=pk)
            
            # Update balance and create transaction atomically
            with transaction.atomic():
                if transaction_type == 'in':
                    user.balance += amount
                else:
                    user.balance -= amount
                user.save()
                
                Transaction.objects.create(
                    user=user,
                    amount=amount,
                    transaction_type=transaction_type,
                    remarks=remarks,
                    status='success'
                )
            
            action = 'credited' if transaction_type == 'in' else 'debited'
            messages.success(request, f'Balance {action} successfully. Amount: Rs {amount}')
            
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid amount: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error adjusting balance: {str(e)}')
    
    return redirect('myadmin:user_detail', pk=pk)


@login_required
def user_transactions(request, pk):
    """List all transactions for a specific user"""
    user = get_object_or_404(User, pk=pk)
    transactions = user.transactions.all().order_by('-created_at')
    
    # Filtering
    type_filter = request.GET.get('type')
    if type_filter in ['in', 'out']:
        transactions = transactions.filter(transaction_type=type_filter)
    
    status_filter = request.GET.get('status')
    if status_filter in ['pending', 'success', 'failed']:
        transactions = transactions.filter(status=status_filter)
    
    paginator = Paginator(transactions, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user': user,
        'page_obj': page_obj,
        'transactions': page_obj,
        'type_filter': type_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/users/transaction_list.html', context)


@login_required
def user_withdrawals(request, pk):
    """List all withdrawals for a specific user"""
    user = get_object_or_404(User, pk=pk)
    withdrawals = user.withdrawals.all().order_by('-created_at')
    
    # Filtering
    status_filter = request.GET.get('status')
    if status_filter in ['pending', 'approved', 'rejected']:
        withdrawals = withdrawals.filter(status=status_filter)
    
    paginator = Paginator(withdrawals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'user': user,
        'page_obj': page_obj,
        'withdrawals': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/users/withdrawal_list.html', context)


@login_required
def user_withdrawal_action(request, pk, withdrawal_pk):
    """Quick action for withdrawal approval/rejection from user page"""
    user = get_object_or_404(User, pk=pk)
    withdrawal = get_object_or_404(Withdrawal, pk=withdrawal_pk, user=user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            if withdrawal.status != 'approved':
                if request.FILES.get('screenshot_prove'):
                    withdrawal.screenshot_prove = request.FILES['screenshot_prove']
                
                remarks = request.POST.get('remarks', '')
                if remarks:
                    withdrawal.remarks = remarks
                
                withdrawal.status = 'approved'
                withdrawal.payment_status = 'paid'
                withdrawal.save()
                
                Transaction.objects.create(
                    user=user,
                    amount=withdrawal.amount,
                    transaction_type='out',
                    remarks=f'Withdrawal Approved (ID: {withdrawal.id})',
                    status='success'
                )
                
                messages.success(request, 'Withdrawal approved successfully.')
        
        elif action == 'reject':
            if withdrawal.status == 'pending':
                # Refund user
                user.balance += withdrawal.amount
                user.save()
                
                Transaction.objects.create(
                    user=user,
                    amount=withdrawal.amount,
                    transaction_type='in',
                    remarks=f'Withdrawal Refund (Rejected ID: {withdrawal.id})',
                    status='success'
                )
            
            reason = request.POST.get('reject_reason', '')
            withdrawal.status = 'rejected'
            withdrawal.payment_status = 'refunded'
            withdrawal.reject_reason = reason
            withdrawal.save()
            messages.success(request, 'Withdrawal rejected and funds refunded.')
    
    return redirect('myadmin:user_detail', pk=pk)


@login_required
def kyc_list(request):
    """List all KYC verification requests"""
    users = User.objects.filter(is_influencer=True).exclude(kyc_status=None)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        users = users.filter(kyc_status=status_filter)
    else:
        # Default to pending if no filter
        users = users.filter(kyc_status='pending')
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(citizenship_no__icontains=search_query)
        )
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'pending': User.objects.filter(is_influencer=True, kyc_status='pending').count(),
        'approved': User.objects.filter(is_influencer=True, kyc_status='approved').count(),
        'rejected': User.objects.filter(is_influencer=True, kyc_status='rejected').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'stats': stats,
    }
    
    return render(request, 'admin/users/kyc_list.html', context)


@login_required
def kyc_approve(request, pk):
    """Approve user KYC verification"""
    user = get_object_or_404(User, pk=pk, is_influencer=True)
    
    if request.method == 'POST':
        user.kyc_status = 'approved'
        user.kyc_reject_reason = None
        user.save()  # This will trigger earn_code generation in save() method
        messages.success(request, f'KYC verification approved for {user.email}. Earn code generated: {user.earn_code}')
        return redirect('myadmin:kyc_list')
    
    return redirect('myadmin:user_detail', pk=pk)


@login_required
def kyc_reject(request, pk):
    """Reject user KYC verification"""
    user = get_object_or_404(User, pk=pk, is_influencer=True)
    
    if request.method == 'POST':
        reject_reason = request.POST.get('reject_reason', '').strip()
        if not reject_reason:
            messages.error(request, 'Rejection reason is required.')
            return redirect('myadmin:user_detail', pk=pk)
        
        user.kyc_status = 'rejected'
        user.kyc_reject_reason = reject_reason
        user.save()
        messages.success(request, f'KYC verification rejected for {user.email}.')
        return redirect('myadmin:kyc_list')
    
    return redirect('myadmin:user_detail', pk=pk)

