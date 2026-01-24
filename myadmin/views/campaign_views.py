from django.shortcuts import render, get_object_or_404, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from core.models import Campaign
from django.forms import modelform_factory
from django import forms


@superuser_required
def campaign_list(request):
    """List all campaigns"""
    campaigns = Campaign.objects.select_related('product').all()
    
    is_active_filter = request.GET.get('is_active')
    if is_active_filter is not None:
        is_active_filter = is_active_filter.lower() == 'true'
        campaigns = campaigns.filter(is_active=is_active_filter)
    
    paginator = Paginator(campaigns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/campaigns/list.html', {
        'page_obj': page_obj,
        'is_active_filter': is_active_filter,
    })


@superuser_required
def campaign_create(request):
    """Create new campaign"""
    CampaignForm = modelform_factory(
        Campaign,
        fields=['product', 'name', 'description', 'image', 'video_link', 'percentage', 'is_active'],
        widgets={
            'product': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'video_link': forms.URLInput(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save()
            messages.success(request, f'Campaign "{campaign.name}" created successfully.')
            return redirect('myadmin:campaign_list')
    else:
        form = CampaignForm()
        
    return render(request, 'admin/campaigns/form.html', {'form': form})


@superuser_required
def campaign_detail(request, pk):
    """View campaign details"""
    campaign = get_object_or_404(Campaign.objects.select_related('product'), pk=pk)
    
    # Get order items with this campaign
    from core.models import OrderItem
    order_items = OrderItem.objects.filter(campaign=campaign).select_related('order', 'product').order_by('-created_at')[:20]
    
    return render(request, 'admin/campaigns/detail.html', {
        'campaign': campaign,
        'order_items': order_items,
    })


@superuser_required
def campaign_edit(request, pk):
    """Edit campaign"""
    campaign = get_object_or_404(Campaign, pk=pk)
    
    CampaignForm = modelform_factory(
        Campaign,
        fields=['product', 'name', 'description', 'image', 'video_link', 'percentage', 'is_active'],
        widgets={
            'product': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'video_link': forms.URLInput(attrs={'class': 'form-control'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, f'Campaign "{campaign.name}" updated successfully.')
            return redirect('myadmin:campaign_list')
    else:
        form = CampaignForm(instance=campaign)
        
    return render(request, 'admin/campaigns/form.html', {'form': form, 'campaign': campaign})


@superuser_required
def campaign_delete(request, pk):
    """Delete campaign"""
    campaign = get_object_or_404(Campaign, pk=pk)
    
    if request.method == 'POST':
        name = campaign.name
        campaign.delete()
        messages.success(request, f'Campaign "{name}" deleted successfully.')
        return redirect('myadmin:campaign_list')
        
    return render(request, 'admin/campaigns/delete.html', {'campaign': campaign})
