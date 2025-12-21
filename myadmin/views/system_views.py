from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Setting, Task, UserTask, UserTaskImage, UserTaskLink, Withdrawal, Transaction, User
from django.forms import modelform_factory
from django import forms

# --- SETTINGS ---
@login_required
def settings_view(request):
    """Manage system settings (Singleton)"""
    # Ensure only one setting object exists or get the first one
    setting = Setting.objects.first()
    if not setting:
        setting = Setting.objects.create()
        
    SettingForm = modelform_factory(
        Setting,
        fields=['system_balance', 'sale_commision', 'is_withdrawal', 'min_withdrawal', 'max_withdrawal', 'low_stock_threshold',
                'email', 'phone', 'address', 'facebook_url', 'instagram_url', 'youtube_url', 'tiktok_url'],
        widgets={
            'system_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sale_commision': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
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


# --- TASKS ---
@login_required
def task_list(request):
    """List all tasks"""
    tasks = Task.objects.all()
    
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/system/task_list.html', {'page_obj': page_obj})

@login_required
def task_create(request):
    """Create new task"""
    TaskForm = modelform_factory(
        Task,
        fields=['social_media', 'title', 'target', 'amount', 'is_active'],
        widgets={
            'social_media': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'target': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" created successfully.')
            return redirect('myadmin:task_list')
    else:
        form = TaskForm()
        
    return render(request, 'admin/system/task_form.html', {'form': form})

@login_required
def task_edit(request, pk):
    """Edit task"""
    task = get_object_or_404(Task, pk=pk)
    
    TaskForm = modelform_factory(
        Task,
        fields=['social_media', 'title', 'target', 'amount', 'is_active'],
        widgets={
            'social_media': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'target': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully.')
            return redirect('myadmin:task_list')
    else:
        form = TaskForm(instance=task)
        
    return render(request, 'admin/system/task_form.html', {'form': form, 'task': task})

@login_required
def task_delete(request, pk):
    """Delete task"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted successfully.')
        return redirect('myadmin:task_list')
        
    return render(request, 'admin/system/task_delete.html', {'task': task})


# --- USER TASKS (SUBMISSIONS) ---
@login_required
def usertask_list(request):
    """List user submissions"""
    usertasks = UserTask.objects.select_related('user', 'task').all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        usertasks = usertasks.filter(status=status_filter)
        
    paginator = Paginator(usertasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/system/usertask_list_v2.html', {
        'page_obj': page_obj,
        'status_filter': status_filter
    })

@login_required
def usertask_detail(request, pk):
    """View submission detail"""
    usertask = get_object_or_404(UserTask.objects.select_related('user', 'task'), pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            if usertask.status != 'approved':
                # Use Transaction to add balance safely
                amount = usertask.task.amount
                user = usertask.user
                
                # Check setting balance? (Optional based on requirements, assuming system generates money or system_balance is a pool)
                setting = Setting.objects.first()
                if setting and setting.system_balance < amount:
                    messages.error(request, 'Insufficient system balance to approve task.')
                    return redirect('myadmin:usertask_detail', pk=pk)

                user.balance += amount
                user.save()
                
                # Deduct from system
                if setting:
                    setting.system_balance -= amount
                    setting.save()

                Transaction.objects.create(
                    user=user,
                    amount=amount,
                    transaction_type='in',
                    remarks=f'Task Reward: {usertask.task.title}',
                    status='success'
                )
                
                usertask.status = 'approved'
                usertask.save()
                messages.success(request, 'Task approved and reward sent.')
                
        elif action == 'reject':
            reason = request.POST.get('reject_reason', '')
            usertask.status = 'rejected'
            usertask.reject_reason = reason
            usertask.save()
            messages.success(request, 'Task rejected.')
            
        return redirect('myadmin:usertask_detail', pk=pk)

    return render(request, 'admin/system/usertask_detail.html', {'usertask': usertask})


# --- WITHDRAWALS ---
@login_required
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

@login_required
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
@login_required
def transaction_list(request):
    """List transactions"""
    transactions = Transaction.objects.select_related('user').all().order_by('-created_at')
    
    paginator = Paginator(transactions, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/system/transaction_list.html', {'page_obj': page_obj})
