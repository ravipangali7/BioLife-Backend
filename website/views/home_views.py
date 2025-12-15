from django.shortcuts import render
from core.models import Banner, Category, Product, Brand


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
