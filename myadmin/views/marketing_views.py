from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Banner, Coupon, CMSPage
from django.forms import modelform_factory
from django import forms


# Banner Views
@login_required
def banner_list(request):
    """List all banners"""
    banners = Banner.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        banners = banners.filter(title__icontains=search_query)
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        banners = banners.filter(is_active=True)
    elif status_filter == 'inactive':
        banners = banners.filter(is_active=False)
    
    paginator = Paginator(banners, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'banners': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/banners/list.html', context)


@login_required
def banner_detail(request, pk):
    """Banner detail view"""
    banner = get_object_or_404(Banner, pk=pk)
    
    context = {
        'banner': banner,
    }
    
    return render(request, 'admin/banners/detail.html', context)


@login_required
def banner_create(request):
    """Create new banner"""
    BannerForm = modelform_factory(
        Banner,
        fields=['title', 'image', 'url', 'is_active'],
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save()
            messages.success(request, f'Banner "{banner.title}" created successfully.')
            return redirect('myadmin:banner_detail', pk=banner.pk)
    else:
        form = BannerForm()
    
    return render(request, 'admin/banners/form.html', {'form': form})


@login_required
def banner_edit(request, pk):
    """Edit banner"""
    banner = get_object_or_404(Banner, pk=pk)
    
    BannerForm = modelform_factory(
        Banner,
        fields=['title', 'image', 'url', 'is_active'],
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            banner = form.save()
            messages.success(request, f'Banner "{banner.title}" updated successfully.')
            return redirect('myadmin:banner_detail', pk=banner.pk)
    else:
        form = BannerForm(instance=banner)
    
    return render(request, 'admin/banners/form.html', {'form': form, 'banner': banner})


@login_required
def banner_delete(request, pk):
    """Delete banner"""
    banner = get_object_or_404(Banner, pk=pk)
    
    if request.method == 'POST':
        banner_title = banner.title
        banner.delete()
        messages.success(request, f'Banner "{banner_title}" deleted successfully.')
        return redirect('myadmin:banner_list')
    
    return render(request, 'admin/banners/delete.html', {'banner': banner})


# Coupon Views
@login_required
def coupon_list(request):
    """List all coupons"""
    coupons = Coupon.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        coupons = coupons.filter(coupon_code__icontains=search_query)
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        coupons = coupons.filter(is_active=True)
    elif status_filter == 'inactive':
        coupons = coupons.filter(is_active=False)
    
    paginator = Paginator(coupons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'coupons': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/coupons/list.html', context)


@login_required
def coupon_detail(request, pk):
    """Coupon detail view"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    context = {
        'coupon': coupon,
        'is_valid': coupon.is_valid(),
    }
    
    return render(request, 'admin/coupons/detail.html', context)


@login_required
def coupon_create(request):
    """Create new coupon"""
    CouponForm = modelform_factory(
        Coupon,
        fields=['coupon_code', 'start_date', 'end_date', 'discount_type', 'discount', 'usage_limit', 'is_active'],
        widgets={
            'coupon_code': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f'Coupon "{coupon.coupon_code}" created successfully.')
            return redirect('myadmin:coupon_detail', pk=coupon.pk)
    else:
        form = CouponForm()
    
    return render(request, 'admin/coupons/form.html', {'form': form})


@login_required
def coupon_edit(request, pk):
    """Edit coupon"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    CouponForm = modelform_factory(
        Coupon,
        fields=['coupon_code', 'start_date', 'end_date', 'discount_type', 'discount', 'usage_limit', 'is_active'],
        widgets={
            'coupon_code': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            coupon = form.save()
            messages.success(request, f'Coupon "{coupon.coupon_code}" updated successfully.')
            return redirect('myadmin:coupon_detail', pk=coupon.pk)
    else:
        form = CouponForm(instance=coupon)
    
    return render(request, 'admin/coupons/form.html', {'form': form, 'coupon': coupon})


@login_required
def coupon_delete(request, pk):
    """Delete coupon"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        coupon_code = coupon.coupon_code
        coupon.delete()
        messages.success(request, f'Coupon "{coupon_code}" deleted successfully.')
        return redirect('myadmin:coupon_list')
    
    return render(request, 'admin/coupons/delete.html', {'coupon': coupon})


# CMS Page Views
@login_required
def cmspage_list(request):
    """List all CMS pages"""
    pages = CMSPage.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        pages = pages.filter(
            Q(title__icontains=search_query) |
            Q(slug__icontains=search_query)
        )
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        pages = pages.filter(is_active=True)
    elif status_filter == 'inactive':
        pages = pages.filter(is_active=False)
    
    paginator = Paginator(pages, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'pages': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/cmspages/list.html', context)


@login_required
def cmspage_detail(request, pk):
    """CMS page detail view"""
    page = get_object_or_404(CMSPage, pk=pk)
    
    context = {
        'page': page,
    }
    
    return render(request, 'admin/cmspages/detail.html', context)


@login_required
def cmspage_create(request):
    """Create new CMS page"""
    CMSPageForm = modelform_factory(
        CMSPage,
        fields=['title', 'slug', 'content', 'is_active', 'image', 'in_footer', 'in_header'],
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'in_footer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = CMSPageForm(request.POST, request.FILES)
        if form.is_valid():
            page = form.save()
            messages.success(request, f'CMS Page "{page.title}" created successfully.')
            return redirect('myadmin:cmspage_detail', pk=page.pk)
    else:
        form = CMSPageForm()
    
    return render(request, 'admin/cmspages/form.html', {'form': form})


@login_required
def cmspage_edit(request, pk):
    """Edit CMS page"""
    page = get_object_or_404(CMSPage, pk=pk)
    
    CMSPageForm = modelform_factory(
        CMSPage,
        fields=['title', 'slug', 'content', 'is_active', 'image', 'in_footer', 'in_header'],
        widgets={
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'in_footer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = CMSPageForm(request.POST, request.FILES, instance=page)
        if form.is_valid():
            page = form.save()
            messages.success(request, f'CMS Page "{page.title}" updated successfully.')
            return redirect('myadmin:cmspage_detail', pk=page.pk)
    else:
        form = CMSPageForm(instance=page)
    
    return render(request, 'admin/cmspages/form.html', {'form': form, 'page': page})


@login_required
def cmspage_delete(request, pk):
    """Delete CMS page"""
    page = get_object_or_404(CMSPage, pk=pk)
    
    if request.method == 'POST':
        page_title = page.title
        page.delete()
        messages.success(request, f'CMS Page "{page_title}" deleted successfully.')
        return redirect('myadmin:cmspage_list')
    
    return render(request, 'admin/cmspages/delete.html', {'page': page})

