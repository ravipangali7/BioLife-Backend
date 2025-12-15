from django.urls import path
from .views import (
    dashboard_views,
    product_views,
    category_views,
    user_views,
    order_views,
    marketing_views,
    brand_views,
    unit_views,
)

app_name = 'myadmin'

urlpatterns = [
    # Dashboard
    path('', dashboard_views.dashboard, name='dashboard'),
    
    # Products
    path('products/', product_views.product_list, name='product_list'),
    path('products/create/', product_views.product_create, name='product_create'),
    path('products/<int:pk>/', product_views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', product_views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', product_views.product_delete, name='product_delete'),
    path('products/<int:product_pk>/images/', product_views.product_image_list, name='product_image_list'),
    path('products/<int:product_pk>/reviews/', product_views.product_review_list, name='product_review_list'),
    
    # Categories
    path('categories/', category_views.category_list, name='category_list'),
    path('categories/create/', category_views.category_create, name='category_create'),
    path('categories/<int:pk>/', category_views.category_detail, name='category_detail'),
    path('categories/<int:pk>/edit/', category_views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', category_views.category_delete, name='category_delete'),
    
    # SubCategories
    path('subcategories/', category_views.subcategory_list, name='subcategory_list'),
    path('subcategories/create/', category_views.subcategory_create, name='subcategory_create'),
    path('subcategories/<int:pk>/', category_views.subcategory_detail, name='subcategory_detail'),
    path('subcategories/<int:pk>/edit/', category_views.subcategory_edit, name='subcategory_edit'),
    path('subcategories/<int:pk>/delete/', category_views.subcategory_delete, name='subcategory_delete'),
    
    # ChildCategories
    path('childcategories/', category_views.childcategory_list, name='childcategory_list'),
    path('childcategories/create/', category_views.childcategory_create, name='childcategory_create'),
    path('childcategories/<int:pk>/', category_views.childcategory_detail, name='childcategory_detail'),
    path('childcategories/<int:pk>/edit/', category_views.childcategory_edit, name='childcategory_edit'),
    path('childcategories/<int:pk>/delete/', category_views.childcategory_delete, name='childcategory_delete'),
    
    # Users
    path('users/', user_views.user_list, name='user_list'),
    path('users/<int:pk>/', user_views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', user_views.user_edit, name='user_edit'),
    path('users/<int:user_pk>/addresses/', user_views.address_list, name='address_list'),
    path('addresses/<int:pk>/', user_views.address_detail, name='address_detail'),
    path('addresses/create/<int:user_pk>/', user_views.address_create, name='address_create'),
    path('addresses/<int:pk>/edit/', user_views.address_edit, name='address_edit'),
    path('addresses/<int:pk>/delete/', user_views.address_delete, name='address_delete'),
    
    # Orders
    path('orders/', order_views.order_list, name='order_list'),
    path('orders/<int:pk>/', order_views.order_detail, name='order_detail'),
    path('orders/<int:pk>/edit/', order_views.order_edit, name='order_edit'),
    path('orders/<int:pk>/delete/', order_views.order_delete, name='order_delete'),
    
    # Banners
    path('banners/', marketing_views.banner_list, name='banner_list'),
    path('banners/create/', marketing_views.banner_create, name='banner_create'),
    path('banners/<int:pk>/', marketing_views.banner_detail, name='banner_detail'),
    path('banners/<int:pk>/edit/', marketing_views.banner_edit, name='banner_edit'),
    path('banners/<int:pk>/delete/', marketing_views.banner_delete, name='banner_delete'),
    
    # Coupons
    path('coupons/', marketing_views.coupon_list, name='coupon_list'),
    path('coupons/create/', marketing_views.coupon_create, name='coupon_create'),
    path('coupons/<int:pk>/', marketing_views.coupon_detail, name='coupon_detail'),
    path('coupons/<int:pk>/edit/', marketing_views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:pk>/delete/', marketing_views.coupon_delete, name='coupon_delete'),
    
    # CMS Pages
    path('cmspages/', marketing_views.cmspage_list, name='cmspage_list'),
    path('cmspages/create/', marketing_views.cmspage_create, name='cmspage_create'),
    path('cmspages/<int:pk>/', marketing_views.cmspage_detail, name='cmspage_detail'),
    path('cmspages/<int:pk>/edit/', marketing_views.cmspage_edit, name='cmspage_edit'),
    path('cmspages/<int:pk>/delete/', marketing_views.cmspage_delete, name='cmspage_delete'),
    
    # Brands
    path('brands/', brand_views.brand_list, name='brand_list'),
    path('brands/create/', brand_views.brand_create, name='brand_create'),
    path('brands/<int:pk>/', brand_views.brand_detail, name='brand_detail'),
    path('brands/<int:pk>/edit/', brand_views.brand_edit, name='brand_edit'),
    path('brands/<int:pk>/delete/', brand_views.brand_delete, name='brand_delete'),
    
    # Units
    path('units/', unit_views.unit_list, name='unit_list'),
    path('units/create/', unit_views.unit_create, name='unit_create'),
    path('units/<int:pk>/', unit_views.unit_detail, name='unit_detail'),
    path('units/<int:pk>/edit/', unit_views.unit_edit, name='unit_edit'),
    path('units/<int:pk>/delete/', unit_views.unit_delete, name='unit_delete'),
]

