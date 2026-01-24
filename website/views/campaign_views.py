from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Campaign, Setting, User
from website.views.earn_views import check_influencer_kyc_access
from django.http import JsonResponse


@login_required
def campaign_list(request):
    """List active campaigns"""
    # Get setting for context
    setting = Setting.objects.first() or Setting.objects.create()
    
    # Check access
    has_access, error_message = check_influencer_kyc_access(request.user)
    
    if not has_access:
        if request.user.is_influencer:
            messages.warning(request, error_message)
            return redirect('website:account_profile')
        else:
            messages.info(request, error_message)
    
    # Get active campaigns
    campaigns = Campaign.objects.filter(is_active=True).select_related('product').order_by('-created_at')
    
    return render(request, 'site/earn/campaign_list.html', {
        'campaigns': campaigns,
        'has_access': has_access,
        'setting': setting,
        'active_referal_system': setting.active_referal_system,
    })


@login_required
def campaign_detail(request, campaign_id):
    """Campaign detail page with enroll button"""
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
            return redirect('website:campaign_list')
    
    campaign = get_object_or_404(Campaign, pk=campaign_id, is_active=True)
    
    # Check if user has earn_code
    user_earn_code = request.user.earn_code if request.user.earn_code else None
    
    return render(request, 'site/earn/campaign_detail.html', {
        'campaign': campaign,
        'user_earn_code': user_earn_code,
        'has_access': has_access,
        'setting': setting,
        'active_referal_system': setting.active_referal_system,
    })


@login_required
def campaign_enroll(request, campaign_id):
    """Generate referral link for campaign enrollment"""
    # Check access
    has_access, error_message = check_influencer_kyc_access(request.user)
    
    if not has_access:
        return JsonResponse({'error': error_message}, status=403)
    
    campaign = get_object_or_404(Campaign, pk=campaign_id, is_active=True)
    
    # Check if user has earn_code
    if not request.user.earn_code:
        return JsonResponse({'error': 'You need to complete KYC verification to get an earn code.'}, status=400)
    
    # Generate referral link
    from django.urls import reverse
    product_url = reverse('website:product_detail', kwargs={'pk': campaign.product.id})
    referral_link = request.build_absolute_uri(
        f"{product_url}?earncode={request.user.earn_code}&campaign={campaign.id}"
    )
    
    return JsonResponse({
        'success': True,
        'referral_link': referral_link,
        'campaign_name': campaign.name,
        'product_name': campaign.product.name,
    })
