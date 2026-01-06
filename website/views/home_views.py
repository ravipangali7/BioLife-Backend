from django.shortcuts import render
from urllib.parse import unquote
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta
from core.models import Banner, Category, Product, Brand, CMSPage, FlashDeal, OrderItem, ProductReview


def home(request):
    """Homepage view with banners, categories, and featured products"""
    from django.utils import timezone
    now = timezone.now()
    
    # Get active banners
    banners = Banner.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Get featured categories
    categories = Category.objects.all()[:8]
    
    # Get featured products
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    
    # Get new arrivals (latest products)
    new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    # Get brands
    brands = Brand.objects.all()[:10]
    
    # Get active flash deals
    active_flash_deals = FlashDeal.objects.filter(
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).order_by('-created_at')[:3]
    
    # Get flash deal products (from all active deals)
    flash_deal_products = Product.objects.filter(
        flash_deals__in=active_flash_deals,
        is_active=True
    ).distinct()[:8]
    
    # Get best sellers (top selling products based on order items)
    best_sellers = Product.objects.filter(
        is_active=True,
        order_items__order__payment_status='paid'
    ).annotate(
        total_sold=Sum('order_items__quantity')
    ).filter(
        total_sold__gt=0
    ).order_by('-total_sold')[:8]
    
    # Get trending products (products with recent orders in last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    trending_products = Product.objects.filter(
        is_active=True,
        order_items__order__created_at__gte=thirty_days_ago,
        order_items__order__payment_status='paid'
    ).annotate(
        recent_orders=Count('order_items__id', distinct=True)
    ).filter(
        recent_orders__gt=0
    ).order_by('-recent_orders', '-created_at')[:8]
    
    # Evaluate trending_products to get IDs first
    trending_products_list = list(trending_products)
    trending_product_ids = [p.id for p in trending_products_list]

    # If not enough trending products, fill with new arrivals
    if len(trending_products_list) < 8:
        additional = Product.objects.filter(
            is_active=True
        ).exclude(
            id__in=trending_product_ids  # Use list of IDs, not subquery
        ).order_by('-created_at')[:8 - len(trending_products_list)]
        trending_products = trending_products_list + list(additional)
    else:
        trending_products = trending_products_list
    
    # Get customer testimonials (recent product reviews with messages)
    testimonials = ProductReview.objects.filter(
        message__isnull=False,
        message__gt=''
    ).select_related('user', 'product').order_by('-created_at')[:6]
    
    context = {
        'banners': banners,
        'categories': categories,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'brands': brands,
        'active_flash_deals': active_flash_deals,
        'flash_deal_products': flash_deal_products,
        'best_sellers': best_sellers,
        'trending_products': trending_products,
        'testimonials': testimonials,
    }
    
    return render(request, 'site/home/index.html', context)


def cms_page_view(request, slug):
    """Display CMS page by slug"""
    # Decode URL-encoded characters (e.g., %26 becomes &)
    decoded_slug = unquote(slug)
    
    try:
        page = CMSPage.objects.get(slug=decoded_slug, is_active=True)
    except CMSPage.DoesNotExist:
        # Render custom 404 page when CMS page is not found
        return render(request, '404.html', status=404)
    
    context = {
        'page': page,
    }
    
    return render(request, 'site/cms/page.html', context)
