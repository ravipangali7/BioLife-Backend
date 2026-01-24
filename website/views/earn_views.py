from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Setting, Withdrawal, Transaction


def check_influencer_kyc_access(user):
    """
    Check if user has access to earn rewards and wallet features.
    Returns: (has_access: bool, error_message: str or None)
    """
    if not user.is_influencer:
        return (False, "This feature is only available for IBOs. Please register as an IBO to access Earn Rewards and Wallet features.")
    
    if user.kyc_status != 'approved':
        if user.kyc_status == 'pending':
            return (False, "Your KYC verification is pending review. Please wait for admin approval to access Earn Rewards and Wallet features.")
        elif user.kyc_status == 'rejected':
            reason = f": {user.kyc_reject_reason}" if user.kyc_reject_reason else ""
            return (False, f"Your KYC verification was rejected{reason}. Please update your documents and resubmit.")
        else:
            return (False, "Please complete your KYC verification in your profile to access Earn Rewards and Wallet features.")
    
    return (True, None)


@login_required
def wallet_view(request):
    """User wallet and withdrawal"""
    # Get setting for context
    setting = Setting.objects.first() or Setting.objects.create()
    
    # Check access
    has_access, error_message = check_influencer_kyc_access(request.user)
    
    if not has_access:
        if request.user.is_influencer:
            messages.warning(request, error_message)
            return redirect('website:account_profile')
        else:
            messages.error(request, error_message)
            return redirect('website:account_dashboard')
    
    user = request.user
    
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
    
    if request.method == 'POST':
        if not setting.is_withdrawal:
            messages.error(request, 'Withdrawals are currently disabled.')
            return redirect('website:wallet')
            
        amount = float(request.POST.get('amount', 0))
        
        # Validation
        if amount < float(setting.min_withdrawal):
            messages.error(request, f'Minimum withdrawal is Rs {setting.min_withdrawal}')
        elif amount > float(setting.max_withdrawal):
            messages.error(request, f'Maximum withdrawal is Rs {setting.max_withdrawal}')
        elif amount > float(user.balance):
            messages.error(request, 'Insufficient balance.')
        else:
            # Create Withdrawal (payment details are stored in user model)
            withdrawal = Withdrawal.objects.create(
                user=user,
                amount=amount,
                payment_status='pending'
            )
            
            # Deduct balance immediately (pending state)
            user.balance = float(user.balance) - amount
            user.save()
            
            Transaction.objects.create(
                user=user,
                amount=amount,
                transaction_type='out',
                remarks=f'Withdrawal Request (ID: {withdrawal.id})',
                status='success' # Transaction success, withdrawal pending
            )
            
            messages.success(request, 'Withdrawal request submitted.')
            return redirect('website:wallet')
            
    return render(request, 'site/earn/wallet.html', {
        'user': user,
        'setting': setting,
        'transactions': transactions,
        'withdrawals': withdrawals,
        'has_access': has_access,
        'active_referal_system': setting.active_referal_system,
    })
