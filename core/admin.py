from django.contrib import admin
from django.utils.html import format_html
from .models import (
    User, Address, ShippingCharge, Unit, Category, SubCategory, ChildCategory,
    Brand, Product, ProductImage, ProductReview, Wishlist, Banner, Coupon,
    CMSPage, Order, OrderItem, PasswordResetOTP, FlashDeal, Campaign
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'phone', 'is_active', 'is_influencer', 'points', 'date_joined']
    list_filter = ['is_active', 'is_influencer', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'name', 'phone']
    readonly_fields = ['date_joined', 'last_login', 'points']
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Information', {
            'fields': ('name', 'phone', 'date_of_birth', 'address', 'image')
        }),
        ('Social Media', {
            'fields': ('is_influencer', 'tiktok_link', 'facebook_link', 'instagram_link', 'youtube_link')
        }),
        ('Payment Information', {
            'fields': ('qr_code', 'esewa_number', 'khalti_number')
        }),
        ('Status & Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Points & Dates', {
            'fields': ('points', 'date_joined', 'last_login')
        }),
    )


@admin.register(ShippingCharge)
class ShippingChargeAdmin(admin.ModelAdmin):
    list_display = ['name', 'charge', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'city', 'shipping_charge', 'state', 'country', 'created_at']
    list_filter = ['country', 'state', 'shipping_charge', 'created_at']
    search_fields = ['title', 'user__email', 'user__name', 'city', 'state', 'country']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['title', 'symbol']
    search_fields = ['title', 'symbol']


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_featured', 'image_preview', 'created_at']
    list_filter = ['is_featured', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    inlines = [SubCategoryInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'image', 'image_preview')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_featured',),
            'description': 'Order determines display sequence (auto-incremented if empty or duplicate). Featured categories will appear in the header category bar'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'


class ChildCategoryInline(admin.TabularInline):
    model = ChildCategory
    extra = 1


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'image_preview', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'category__name']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    inlines = [ChildCategoryInline]
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'


@admin.register(ChildCategory)
class ChildCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'sub_category', 'category_name', 'image_preview', 'created_at']
    list_filter = ['sub_category__category', 'created_at']
    search_fields = ['name', 'sub_category__name', 'sub_category__category__name']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    def category_name(self, obj):
        return obj.sub_category.category.name
    category_name.short_description = 'Category'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'logo_preview', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'logo_preview']
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "No Logo"
    logo_preview.short_description = 'Logo'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'brand', 'regular_price', 'final_price_display', 'stock', 'is_active', 'is_featured', 'image_preview']
    list_filter = ['is_active', 'is_featured', 'category', 'brand', 'discount_type', 'created_at']
    search_fields = ['name', 'sku', 'short_description']
    readonly_fields = ['created_at', 'updated_at', 'image_preview', 'final_price_display']
    inlines = [ProductImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'image', 'image_preview', 'short_description', 'long_description')
        }),
        ('Categorization', {
            'fields': ('category', 'sub_category', 'child_category', 'brand', 'unit')
        }),
        ('Pricing & Stock', {
            'fields': ('regular_price', 'discount_type', 'discount', 'final_price_display', 'stock')
        }),
        ('Variants', {
            'fields': ('product_varient',),
            'description': 'JSON format: {"variant_name": "Color", "variant_values": ["red", "blue"], "combinations": {"red/xl": {"price": 100, "stock": 10, "image": "url"}}}'
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'
    
    def final_price_display(self, obj):
        price = obj.get_final_price()
        return f"${price:.2f}"
    final_price_display.short_description = 'Final Price'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'product__sku']
    readonly_fields = ['created_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'star', 'created_at']
    list_filter = ['star', 'created_at']
    search_fields = ['product__name', 'user__email', 'message']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__name', 'product__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_preview', 'url', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['coupon_code', 'discount_type', 'discount', 'usage', 'usage_limit', 'is_active', 'is_valid_display', 'start_date', 'end_date']
    list_filter = ['discount_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['coupon_code']
    readonly_fields = ['created_at', 'updated_at', 'is_valid_display']
    
    def is_valid_display(self, obj):
        is_valid = obj.is_valid()
        color = 'green' if is_valid else 'red'
        text = 'Valid' if is_valid else 'Invalid'
        return format_html('<span style="color: {};">{}</span>', color, text)
    is_valid_display.short_description = 'Status'


@admin.register(FlashDeal)
class FlashDealAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_type', 'discount', 'product_count', 'is_active', 'is_active_now_display', 'start_time', 'end_time', 'created_at']
    list_filter = ['discount_type', 'is_active', 'start_time', 'end_time', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at', 'is_active_now_display', 'product_count']
    filter_horizontal = ['products']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'image', 'is_active')
        }),
        ('Products', {
            'fields': ('products', 'product_count'),
            'description': 'Select products included in this flash deal'
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'is_active_now_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def is_active_now_display(self, obj):
        is_active = obj.is_active_now()
        color = 'green' if is_active else 'red'
        text = 'Active Now' if is_active else 'Not Active'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)
    is_active_now_display.short_description = 'Current Status'
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'reward_display', 'is_active', 'image_preview', 'created_at']
    list_filter = ['is_active', 'commission_type', 'created_at']
    search_fields = ['name', 'product__name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'name', 'description', 'image', 'image_preview')
        }),
        ('Media', {
            'fields': ('video_link',)
        }),
        ('Reward', {
            'fields': ('commission_type', 'commission_value')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def reward_display(self, obj):
        if obj.commission_type == 'percentage':
            return f'{obj.commission_value}%'
        return f'Rs {obj.commission_value} flat'
    reward_display.short_description = 'Reward'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'


@admin.register(CMSPage)
class CMSPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active', 'in_footer', 'footer_section', 'in_header', 'image_preview', 'created_at']
    list_filter = ['is_active', 'in_footer', 'footer_section', 'in_header', 'created_at']
    search_fields = ['title', 'slug', 'content']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'content', 'image', 'image_preview')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'in_header', 'in_footer', 'footer_section'),
            'description': 'Select where this page should appear. Footer section is required if "In Footer" is checked.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'payment_status', 'order_status', 'payment_method', 'sub_total', 'shipping', 'total', 'created_at']
    list_filter = ['payment_status', 'order_status', 'payment_method', 'created_at']
    search_fields = ['user__email', 'user__name', 'id']
    readonly_fields = ['created_at', 'updated_at', 'total']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'payment_status', 'order_status', 'payment_method')
        }),
        ('Addresses', {
            'fields': ('billing_address', 'shipping_address')
        }),
        ('Shipping', {
            'fields': ('shipping_charge',)
        }),
        ('Pricing', {
            'fields': ('sub_total', 'shipping', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'product_varient', 'quantity', 'price', 'total', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__id', 'product__name', 'product__sku']
    readonly_fields = ['total', 'created_at']


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ['email', 'otp_code', 'is_used', 'is_expired_display', 'expires_at', 'created_at']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['email', 'otp_code', 'token']
    readonly_fields = ['created_at', 'is_expired_display']
    date_hierarchy = 'created_at'
    
    def is_expired_display(self, obj):
        is_expired = obj.is_expired()
        color = 'red' if is_expired else 'green'
        text = 'Expired' if is_expired else 'Valid'
        return format_html('<span style="color: {};">{}</span>', color, text)
    is_expired_display.short_description = 'Status'
