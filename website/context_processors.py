from django.db.models import Q
from core.models import Category, CMSPage, Wishlist, Setting


def cart_count(request):
    """Add cart item count to context"""
    cart = request.session.get('cart', {})
    items = cart.get('items', [])
    count = sum(item.get('quantity', 0) for item in items)
    return {'cart_count': count}


def wishlist_count(request):
    """Add wishlist item count to context"""
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'wishlist_count': count}


def categories(request):
    """Add categories to context for navigation"""
    categories_list = Category.objects.all()[:10]  # Limit for navigation
    return {'nav_categories': categories_list}


def cms_pages(request):
    """Add CMS pages to context for footer"""
    all_pages = CMSPage.objects.filter(is_active=True, in_footer=True).order_by('title')
    customer_service_pages = all_pages.filter(footer_section='customer_service')
    information_pages = all_pages.filter(
        Q(footer_section='information') | Q(footer_section__isnull=True) | Q(footer_section='')
    )
    
    return {
        'cms_pages': all_pages,
        'customer_service_pages': customer_service_pages,
        'information_pages': information_pages,
    }


def site_settings(request):
    """Add site settings to context for all templates"""
    setting = Setting.objects.first()
    return {'site_settings': setting}
