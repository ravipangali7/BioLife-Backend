from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import (
    User, Product, Order, OrderItem, Category, 
    SubCategory, ChildCategory, Brand, Banner, Coupon, Setting
)
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


@login_required
def dashboard(request):
    """Dashboard view with analytics"""
    
    # Calculate statistics
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    
    # Calculate total sales (sum of all order totals)
    total_sales = Order.objects.aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Recent orders (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_orders = Order.objects.filter(
        created_at__gte=seven_days_ago
    ).count()
    
    # Orders by status
    pending_orders = Order.objects.filter(order_status='pending').count()
    processing_orders = Order.objects.filter(order_status='processing').count()
    shipped_orders = Order.objects.filter(order_status='shipped').count()
    delivered_orders = Order.objects.filter(order_status='delivered').count()
    
    # Active products
    active_products = Product.objects.filter(is_active=True).count()
    featured_products = Product.objects.filter(is_featured=True).count()
    
    # Recent orders for table
    recent_orders_list = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Categories count
    categories_count = Category.objects.count()
    subcategories_count = SubCategory.objects.count()
    childcategories_count = ChildCategory.objects.count()
    
    # Active banners
    active_banners = Banner.objects.filter(is_active=True).count()
    
    # Active coupons
    active_coupons = Coupon.objects.filter(is_active=True).count()
    
    # Get global low stock threshold from settings
    setting = Setting.objects.first()
    low_stock_threshold = setting.low_stock_threshold if setting else 10
    
    # Inventory statistics
    low_stock_count = Product.objects.filter(
        stock__gt=0,
        stock__lte=low_stock_threshold,
        is_active=True
    ).count()
    
    out_of_stock_count = Product.objects.filter(stock=0, is_active=True).count()
    
    # Calculate total inventory value
    total_inventory_value = Decimal('0.00')
    for product in Product.objects.filter(is_active=True):
        total_inventory_value += Decimal(str(product.regular_price)) * product.stock
    
    # Low stock alerts
    low_stock_products = Product.objects.filter(
        stock__gt=0,
        stock__lte=low_stock_threshold,
        is_active=True
    ).order_by('stock')[:5]
    
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'active_products': active_products,
        'featured_products': featured_products,
        'recent_orders_list': recent_orders_list,
        'categories_count': categories_count,
        'subcategories_count': subcategories_count,
        'childcategories_count': childcategories_count,
        'active_banners': active_banners,
        'active_coupons': active_coupons,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_inventory_value': total_inventory_value,
        'low_stock_products': low_stock_products,
        'low_stock_threshold': low_stock_threshold,
    }
    
    return render(request, 'admin/dashboard.html', context)

