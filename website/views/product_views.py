from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from core.models import Product, ProductReview, Category, SubCategory, ChildCategory, Brand, OrderItem, Wishlist, User, Setting
from website.views.earn_views import check_influencer_kyc_access


def can_user_review_product(user, product):
    """Check if user can review a product (must have purchased with paid and delivered order)"""
    if not user.is_authenticated:
        return False
    return OrderItem.objects.filter(
        order__user=user,
        product=product,
        order__payment_status='paid',
        order__order_status='delivered'
    ).exists()


def product_list(request):
    """Product listing with filters and search"""
    products = Product.objects.filter(is_active=True)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Category filter - support multiple selections (parent, sub, child)
    category_ids = request.GET.getlist('category')
    subcategory_ids = request.GET.getlist('subcategory')
    childcategory_ids = request.GET.getlist('childcategory')
    
    category_q = Q()
    
    # Filter by parent categories
    if category_ids:
        for cat_id in category_ids:
            try:
                cat_id_int = int(cat_id)
                # Match products in parent category, its subcategories, or child categories
                category_q |= (
                    Q(category_id=cat_id_int) |
                    Q(sub_category__category_id=cat_id_int) |
                    Q(child_category__sub_category__category_id=cat_id_int)
                )
            except ValueError:
                continue
    
    # Filter by subcategories
    if subcategory_ids:
        for subcat_id in subcategory_ids:
            try:
                subcat_id_int = int(subcat_id)
                category_q |= (
                    Q(sub_category_id=subcat_id_int) |
                    Q(child_category__sub_category_id=subcat_id_int)
                )
            except ValueError:
                continue
    
    # Filter by child categories
    if childcategory_ids:
        for childcat_id in childcategory_ids:
            try:
                childcat_id_int = int(childcat_id)
                category_q |= Q(child_category_id=childcat_id_int)
            except ValueError:
                continue
    
    if category_q:
        products = products.filter(category_q).distinct()
    
    # Brand filter - support multiple selections
    brand_ids = request.GET.getlist('brand')
    if brand_ids:
        try:
            brand_ids_int = [int(bid) for bid in brand_ids]
            products = products.filter(brand_id__in=brand_ids_int)
        except ValueError:
            pass
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(regular_price__gte=min_price)
    if max_price:
        products = products.filter(regular_price__lte=max_price)
    
    # Sort
    sort_by = request.GET.get('sort', 'created_at')
    if sort_by == 'price_asc':
        products = products.order_by('regular_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-regular_price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options with hierarchy
    categories = Category.objects.prefetch_related('sub_categories__child_categories').order_by('order', 'name')
    brands = Brand.objects.all()
    
    # Get selected IDs for template
    selected_category_ids = [int(cid) for cid in category_ids if cid.isdigit()]
    selected_subcategory_ids = [int(sid) for sid in subcategory_ids if sid.isdigit()]
    selected_childcategory_ids = [int(cid) for cid in childcategory_ids if cid.isdigit()]
    selected_brand_ids = [int(bid) for bid in brand_ids if bid.isdigit()]
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'search_query': search_query,
        'categories': categories,
        'brands': brands,
        'selected_category_ids': selected_category_ids,
        'selected_subcategory_ids': selected_subcategory_ids,
        'selected_childcategory_ids': selected_childcategory_ids,
        'selected_brand_ids': selected_brand_ids,
        'sort_by': sort_by,
    }
    
    return render(request, 'site/products/list.html', context)


def product_detail(request, pk, earn_code=None):
    """Product detail page with variants and reviews. Supports affiliate links."""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    # If earn_code is provided, validate and store in session
    affiliate_user = None
    if earn_code:
        try:
            affiliate_user = User.objects.get(earn_code=earn_code, is_influencer=True, kyc_status='approved')
            # Store earn_code in session for cart/checkout tracking
            request.session['affiliate_earn_code'] = earn_code
            request.session.modified = True
        except User.DoesNotExist:
            messages.warning(request, 'Invalid affiliate link')
            return redirect('website:product_detail', pk=pk)
    
    # Get product images
    product_images = product.images.all()
    
    # Get reviews
    reviews = ProductReview.objects.filter(product=product).order_by('-created_at')[:10]
    
    # Calculate average rating
    avg_rating = reviews.aggregate(
        avg=Avg('star')
    )['avg'] or 0
    
    # Get related products (same category)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(pk=product.pk)[:4]
    
    # Prepare variant data as JSON for JavaScript
    variant_data_json = json.dumps(product.product_varient) if product.product_varient else '{}'
    
    # Check if user can review this product
    can_review = False
    user_review = None
    is_in_wishlist = False
    can_earn = False
    user_earn_code = None
    commission_percent = None
    
    if request.user.is_authenticated:
        can_review = can_user_review_product(request.user, product)
        if can_review:
            user_review = ProductReview.objects.filter(user=request.user, product=product).first()
        # Check if product is in user's wishlist
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        
        # Check if user can earn from this product (influencer with approved KYC)
        has_access, _ = check_influencer_kyc_access(request.user)
        if has_access:
            can_earn = True
            user_earn_code = request.user.earn_code
            setting = Setting.objects.first()
            if setting:
                commission_percent = setting.sale_commision
    
    context = {
        'product': product,
        'product_images': product_images,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'related_products': related_products,
        'variant_data_json': variant_data_json,
        'can_review': can_review,
        'user_review': user_review,
        'is_in_wishlist': is_in_wishlist,
        'can_earn': can_earn,
        'user_earn_code': user_earn_code,
        'commission_percent': commission_percent,
        'affiliate_user': affiliate_user,
        'is_affiliate_link': bool(earn_code),
    }
    
    return render(request, 'site/products/detail.html', context)


@login_required
def submit_review(request, pk):
    """Submit product review"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    # Check if user can review
    if not can_user_review_product(request.user, product):
        messages.error(request, 'You can only review products you have purchased and received.')
        return redirect('website:product_detail', pk=pk)
    
    # Check if user already reviewed
    existing_review = ProductReview.objects.filter(user=request.user, product=product).first()
    
    if request.method == 'POST':
        star = int(request.POST.get('star', 0))
        message = request.POST.get('message', '').strip()
        
        if star < 1 or star > 5:
            messages.error(request, 'Please select a valid rating (1-5 stars)')
            return redirect('website:product_detail', pk=pk)
        
        if existing_review:
            # Update existing review
            existing_review.star = star
            existing_review.message = message
            existing_review.save()
            messages.success(request, 'Your review has been updated')
        else:
            # Create new review
            ProductReview.objects.create(
                user=request.user,
                product=product,
                star=star,
                message=message
            )
            messages.success(request, 'Thank you for your review!')
    
    return redirect('website:product_detail', pk=pk)
