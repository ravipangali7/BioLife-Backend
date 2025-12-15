from core.models import Category, CMSPage, Wishlist


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
    pages = CMSPage.objects.filter(is_active=True, in_footer=True).order_by('title')
    return {'cms_pages': pages}
