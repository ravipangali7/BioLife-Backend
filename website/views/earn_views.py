from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from core.models import Task, UserTask, UserTaskImage, UserTaskLink, Setting, Withdrawal, Transaction
from django.core.paginator import Paginator


def check_influencer_kyc_access(user):
    """
    Check if user has access to earn rewards and wallet features.
    Returns: (has_access: bool, error_message: str or None)
    """
    if not user.is_influencer:
        return (False, "This feature is only available for influencers. Please register as an influencer to access Earn Rewards and Wallet features.")
    
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
def task_list(request):
    """List available tasks and user history"""
    # Check access
    has_access, error_message = check_influencer_kyc_access(request.user)
    
    if not has_access:
        if request.user.is_influencer:
            # Influencer without KYC - redirect to profile
            messages.warning(request, error_message)
            return redirect('website:account_profile')
        else:
            # Customer - show page but with restrictions
            messages.info(request, error_message)
    
    # Get active tasks
    tasks = Task.objects.filter(is_active=True).order_by('-created_at')
    
    # Get user's submissions to check status
    user_submissions = UserTask.objects.filter(user=request.user)
    submission_map = {sub.task_id: sub for sub in user_submissions}
    
    # Check if user needs to do KYC
    kyc_verified = request.user.kyc_status == 'approved'
    
    return render(request, 'site/earn/task_list.html', {
        'tasks': tasks,
        'submission_map': submission_map,
        'kyc_verified': kyc_verified,
        'has_access': has_access,
        'is_influencer': request.user.is_influencer,
        'kyc_status': request.user.kyc_status
    })

@login_required
def task_detail(request, task_id):
    """Task details and submission form"""
    # Check access
    has_access, error_message = check_influencer_kyc_access(request.user)
    
    if not has_access:
        if request.user.is_influencer:
            messages.warning(request, error_message)
            return redirect('website:account_profile')
        else:
            messages.error(request, error_message)
            return redirect('website:task_list')
    
    task = get_object_or_404(Task, pk=task_id, is_active=True)
    
    # Check if already submitted
    existing_submission = UserTask.objects.filter(user=request.user, task=task).first()
    
    if request.method == 'POST':
        if existing_submission and existing_submission.status != 'rejected':
            messages.warning(request, 'You have already submitted this task.')
            return redirect('website:task_list')
            
        # Create or Update submission
        if not existing_submission:
            submission = UserTask.objects.create(
                user=request.user,
                task=task,
                status='pending',
                description=request.POST.get('description', '')
            )
        else:
            # Re-submit if rejected
            submission = existing_submission
            submission.status = 'pending'
            submission.description = request.POST.get('description', '')
            submission.save()
            
        # Handle proofs
        # Handle proofs
        # Images
        images = request.FILES.getlist('proof_images')
        img_titles = request.POST.getlist('proof_image_titles')
        img_descs = request.POST.getlist('proof_image_descriptions')
        
        # Use zip to pair each image with its corresponding title and description
        # We assume the frontend enforces that every file input has a file (required attribute)
        # thus maintaining the order and count.
        for image, title, desc in zip(images, img_titles, img_descs):
            UserTaskImage.objects.create(
                user_task=submission,
                image=image,
                title=title,
                description=desc
            )
            
        # Links
        links = request.POST.getlist('proof_links')
        link_titles = request.POST.getlist('proof_link_titles')
        link_descs = request.POST.getlist('proof_link_descriptions')
        
        for url, title, desc in zip(links, link_titles, link_descs):
            if url and url.strip():  # Only save non-empty links
                UserTaskLink.objects.create(
                    user_task=submission,
                    url=url,
                    title=title,
                    description=desc
                )
            
        messages.success(request, 'Task submitted successfully! Wait for approval.')
        return redirect('website:task_list')
        
    return render(request, 'site/earn/task_detail.html', {
        'task': task,
        'submission': existing_submission
    })

@login_required
def wallet_view(request):
    """User wallet and withdrawal"""
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
    setting = Setting.objects.first() or Setting.objects.create()
    
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
        'has_access': has_access
    })
