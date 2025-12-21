from django.shortcuts import render
from urllib.parse import unquote
from core.models import Banner, Category, Product, Brand, CMSPage


def home(request):
    """Homepage view with banners, categories, and featured products"""
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
    
    context = {
        'banners': banners,
        'categories': categories,
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'brands': brands,
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
