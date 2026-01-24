from django.shortcuts import render, get_object_or_404, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Setting, Withdrawal, Transaction, User
from django.forms import modelform_factory
from django import forms

# --- SETTINGS ---
@superuser_required
def settings_view(request):
    """Manage system settings (Singleton)"""
    # Ensure only one setting object exists or get the first one
    setting = Setting.objects.first()
    if not setting:
        setting = Setting.objects.create()
        
    SettingForm = modelform_factory(
        Setting,
        fields=['system_balance', 'user_refer_amount', 'active_referal_system', 'is_withdrawal', 'min_withdrawal', 'max_withdrawal', 'low_stock_threshold',
                'email', 'phone', 'address', 'facebook_url', 'instagram_url', 'youtube_url', 'tiktok_url'],
        widgets={
            'system_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'user_refer_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'active_referal_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_withdrawal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'min_withdrawal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_withdrawal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control'}),
            'tiktok_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = SettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, 'System settings updated successfully.')
            return redirect('myadmin:settings_view')
    else:
        form = SettingForm(instance=setting)
        
    return render(request, 'admin/system/settings.html', {'form': form, 'setting': setting})


# --- WITHDRAWALS ---
@superuser_required
def withdrawal_list(request):
    """List withdrawals"""
    withdrawals = Withdrawal.objects.select_related('user').all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        withdrawals = withdrawals.filter(status=status_filter)
        
    paginator = Paginator(withdrawals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/system/withdrawal_list_v2.html', {
        'page_obj': page_obj,
        'status_filter': status_filter
    })

@superuser_required
def withdrawal_detail(request, pk):
    """Withdrawal detail and action"""
    withdrawal = get_object_or_404(Withdrawal.objects.select_related('user'), pk=pk)
    
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
                    user=withdrawal.user,
                    amount=withdrawal.amount,
                    transaction_type='out',
                    remarks=f'Withdrawal Approved (ID: {withdrawal.id})',
                    status='success'
                )
                
                messages.success(request, 'Withdrawal approved.')
                
        elif action == 'reject':
            if withdrawal.status == 'pending':
                # Refund user
                withdrawal.user.balance += withdrawal.amount
                withdrawal.user.save()
                
                Transaction.objects.create(
                    user=withdrawal.user,
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
            
        return redirect('myadmin:withdrawal_detail', pk=pk)

    return render(request, 'admin/system/withdrawal_detail.html', {'withdrawal': withdrawal})


# --- TRANSACTIONS ---
@superuser_required
def transaction_list(request):
    """List transactions"""
    transactions = Transaction.objects.select_related('user').all().order_by('-created_at')
    
    paginator = Paginator(transactions, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/system/transaction_list.html', {'page_obj': page_obj})
