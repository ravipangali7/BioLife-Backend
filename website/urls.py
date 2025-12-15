from django.urls import path
from .views import (
    home_views,
    product_views,
    cart_views,
    checkout_views,
    auth_views,
    account_views,
    category_views,
    brand_views,
)
from django.contrib.auth import views as django_auth_views

app_name = 'website'

urlpatterns = [
    # Home
    path('', home_views.home, name='home'),
    
    # Products
    path('products/', product_views.product_list, name='product_list'),
    path('products/<int:pk>/', product_views.product_detail, name='product_detail'),
    path('products/<int:pk>/review/', product_views.submit_review, name='submit_review'),
    
    # Cart
    path('cart/', cart_views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', cart_views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_index>/', cart_views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_index>/', cart_views.remove_from_cart, name='remove_from_cart'),
    path('cart/coupon/', cart_views.apply_coupon, name='apply_coupon'),
    
    # Checkout
    path('checkout/', checkout_views.checkout, name='checkout'),
    path('checkout/success/<int:order_id>/', checkout_views.checkout_success, name='checkout_success'),
    
    # Authentication
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('logout/', django_auth_views.LogoutView.as_view(), name='logout'),
    
    # Account
    path('account/', account_views.account_dashboard, name='account_dashboard'),
    path('account/profile/', account_views.account_profile, name='account_profile'),
    path('account/orders/', account_views.account_orders, name='account_orders'),
    path('account/orders/<int:order_id>/', account_views.account_order_detail, name='account_order_detail'),
    path('account/addresses/', account_views.account_addresses, name='account_addresses'),
    path('account/addresses/create/', account_views.account_address_create, name='account_address_create'),
    path('account/addresses/<int:address_id>/edit/', account_views.account_address_edit, name='account_address_edit'),
    path('account/addresses/<int:address_id>/delete/', account_views.account_address_delete, name='account_address_delete'),
    
    # Wishlist
    path('account/wishlist/', account_views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', account_views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', account_views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Categories
    path('category/', category_views.category_list, name='category_list'),
    path('category/<int:category_id>/', category_views.category_list, name='category_detail'),
    path('category/<int:category_id>/<int:subcategory_id>/', category_views.subcategory_list, name='subcategory_detail'),
    
    # Brands
    path('brand/<int:brand_id>/', brand_views.brand_list, name='brand_detail'),
]
