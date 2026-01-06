from django.db import models
import random
import string
import time

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, name, password=None, **extra_fields):
        """Create and save a regular user with email and name"""
        if not email:
            raise ValueError('The Email field must be set')
        if not name:
            raise ValueError('The Name field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, password=None, **extra_fields):
        """Create and save a superuser with email and name"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with email as username"""
    username = None  # Remove username field
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_influencer = models.BooleanField(default=False)
    tiktok_link = models.URLField(blank=True, null=True)
    facebook_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)
    youtube_link = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='users/', blank=True, null=True)
    points = models.IntegerField(default=0)
    
    # New fields
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    citizenship_front = models.ImageField(upload_to='kyc/', blank=True, null=True)
    citizenship_back = models.ImageField(upload_to='kyc/', blank=True, null=True)
    citizenship_no = models.CharField(max_length=50, blank=True, null=True)
    earn_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    
    # KYC Status fields
    KYC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]   
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, blank=True, null=True, default=None)
    kyc_reject_reason = models.TextField(blank=True, null=True)
    
    # Payment Information
    qr_code = models.ImageField(upload_to='users/payment/qr/', blank=True, null=True)
    esewa_number = models.CharField(max_length=50, blank=True, null=True)
    khalti_number = models.CharField(max_length=50, blank=True, null=True)

    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
        
    def generate_earn_code(self):
        """Generate unique 10-char earn code"""
        while True:
            # Last 2 digits of timestamp, 4 letters, 4 numbers
            timestamp_part = str(int(time.time()))[-2:]
            letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            numbers = ''.join(random.choices(string.digits, k=4))
            
            # Combine and shuffle slightly or just concat logic
            # User said "also at back very uqniue" - keeping it simple but unique
            code = f"{letters}{timestamp_part}{numbers}"
            
            if not User.objects.filter(earn_code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        # Auto generate earn_code if kyc_status is approved and no code yet
        if self.kyc_status == 'approved' and not self.earn_code:
            self.earn_code = self.generate_earn_code()
        super().save(*args, **kwargs)


class Address(models.Model):
    """User addresses for billing and shipping"""
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"


class Unit(models.Model):
    """Product measurement units"""
    title = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    
    class Meta:
        verbose_name = 'Unit'
        verbose_name_plural = 'Units'
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title} ({self.symbol})"


class Category(models.Model):
    """Main product category"""
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SubCategory(models.Model):
    """Sub category under main category"""
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sub_categories')
    image = models.ImageField(upload_to='sub_categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Sub Category'
        verbose_name_plural = 'Sub Categories'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class ChildCategory(models.Model):
    """Child category under sub category"""
    name = models.CharField(max_length=255)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='child_categories')
    image = models.ImageField(upload_to='child_categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Child Category'
        verbose_name_plural = 'Child Categories'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.sub_category.category.name} - {self.sub_category.name} - {self.name}"


class Brand(models.Model):
    """Product brands"""
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Main product model with variant system"""
    DISCOUNT_TYPE_CHOICES = [
        ('flat', 'Flat'),
        ('percentage', 'Percentage'),
    ]
    
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    child_category = models.ForeignKey(ChildCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    short_description = models.TextField(blank=True, null=True)
    long_description = models.TextField(blank=True, null=True)
    regular_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    # JSON structure: {"variant_name": "Color", "variant_values": ["red", "blue"], 
    # "combinations": {"red/xl": {"price": 100, "stock": 10, "image": "url"}, ...}}
    product_varient = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to calculate stock and price from variants if enabled"""
        # Check if variants are enabled
        if self.product_varient and self.product_varient.get('enabled', False):
            combinations = self.product_varient.get('combinations', {})
            if combinations:
                # Calculate total stock from all combinations
                total_stock = sum(
                    combo.get('stock', 0) 
                    for combo in combinations.values() 
                    if isinstance(combo, dict)
                )
                self.stock = total_stock
                
                # Set regular_price from is_primary variant
                for combo_key, combo_data in combinations.items():
                    if isinstance(combo_data, dict) and combo_data.get('is_primary', False):
                        primary_price = combo_data.get('price', 0)
                        if primary_price:
                            self.regular_price = primary_price
                        break
        
        super().save(*args, **kwargs)
    
    def get_final_price(self, variant_combination=None):
        """Calculate final price considering discount, variant, and flash deals"""
        base_price = float(self.regular_price)
        
        # Get base price from variant if specified
        if variant_combination and self.product_varient:
            combinations = self.product_varient.get('combinations', {})
            if variant_combination in combinations:
                variant_data = combinations[variant_combination]
                if isinstance(variant_data, dict):
                    base_price = float(variant_data.get('price', self.regular_price))
                    
                    # Apply variant-level discount if available
                    variant_discount_type = variant_data.get('discount_type', '')
                    variant_discount = float(variant_data.get('discount', 0))
                    
                    if variant_discount_type == 'flat' and variant_discount > 0:
                        base_price = base_price - variant_discount
                    elif variant_discount_type == 'percentage' and variant_discount > 0:
                        base_price = base_price * (1 - variant_discount / 100)
                    
                    # Check for active flash deal (flash deals override variant discounts)
                    active_flash_deal = self.get_active_flash_deal()
                    if active_flash_deal:
                        if active_flash_deal.discount_type == 'flat':
                            final_price = base_price - float(active_flash_deal.discount)
                        elif active_flash_deal.discount_type == 'percentage':
                            final_price = base_price * (1 - float(active_flash_deal.discount) / 100)
                        else:
                            final_price = base_price
                        return max(0, final_price)
                    
                    # Return variant price with variant discount applied
                    return max(0, base_price)
        
        # Check for active flash deal first (flash deals override product discounts)
        active_flash_deal = self.get_active_flash_deal()
        if active_flash_deal:
            if active_flash_deal.discount_type == 'flat':
                final_price = base_price - float(active_flash_deal.discount)
            elif active_flash_deal.discount_type == 'percentage':
                final_price = base_price * (1 - float(active_flash_deal.discount) / 100)
            else:
                final_price = base_price
            return max(0, final_price)
        
        # Apply product-level discount if no flash deal
        if self.discount_type == 'flat':
            final_price = base_price - float(self.discount)
        elif self.discount_type == 'percentage':
            final_price = base_price * (1 - float(self.discount) / 100)
        else:
            final_price = base_price
        
        return max(0, final_price)  # Ensure price is not negative
    
    def get_active_flash_deal(self):
        """Get active flash deal for this product if any"""
        from django.utils import timezone
        now = timezone.now()
        active_deals = self.flash_deals.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        ).first()
        return active_deals
    
    def get_variant_stock(self, variant_combination=None):
        """Get stock for specific variant combination"""
        if variant_combination and self.product_varient:
            combinations = self.product_varient.get('combinations', {})
            if variant_combination in combinations:
                return combinations[variant_combination].get('stock', self.stock)
        return self.stock
    
    def is_low_stock(self):
        """Check if product is low on stock"""
        # Import Setting here to avoid circular import
        from django.apps import apps
        Setting = apps.get_model('core', 'Setting')
        setting = Setting.objects.first()
        threshold = setting.low_stock_threshold if setting else 10
        return self.stock <= threshold
    
    def is_out_of_stock(self):
        """Check if product is out of stock"""
        return self.stock <= 0
    
    def get_stock_status(self):
        """Get stock status string"""
        if self.is_out_of_stock():
            return 'out_of_stock'
        elif self.is_low_stock():
            return 'low_stock'
        return 'in_stock'


class ProductImage(models.Model):
    """Additional product images"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


class ProductReview(models.Model):
    """Customer product reviews"""
    star = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'
        ordering = ['-created_at']
        unique_together = ['user', 'product']  # One review per user per product
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name} - {self.star} stars"


class Wishlist(models.Model):
    """User wishlist for saving favorite products"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        ordering = ['-created_at']
        unique_together = ['user', 'product']  # One wishlist entry per user per product
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name}"


class Banner(models.Model):
    """Homepage banners"""
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='banners/')
    url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Coupon(models.Model):
    """Discount coupons"""
    DISCOUNT_TYPE_CHOICES = [
        ('flat', 'Flat'),
        ('percentage', 'Percentage'),
    ]
    
    coupon_code = models.CharField(max_length=50, unique=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    usage_limit = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    usage = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.coupon_code
    
    def is_valid(self):
        """Check if coupon is valid"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            self.usage < self.usage_limit
        )


class FlashDeal(models.Model):
    """Flash deals with time-limited offers on products"""
    DISCOUNT_TYPE_CHOICES = [
        ('flat', 'Flat'),
        ('percentage', 'Percentage'),
    ]
    
    title = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, related_name='flash_deals')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='flash_deals/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Flash Deal'
        verbose_name_plural = 'Flash Deals'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_active_now(self):
        """Check if flash deal is currently active"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.start_time <= now <= self.end_time
        )
    
    def get_remaining_time(self):
        """Calculate time remaining until deal ends (in seconds)"""
        from django.utils import timezone
        now = timezone.now()
        if now < self.start_time:
            return None  # Deal hasn't started yet
        if now > self.end_time:
            return 0  # Deal has ended
        delta = self.end_time - now
        return int(delta.total_seconds())


class CMSPage(models.Model):
    """Content management system pages"""
    FOOTER_SECTION_CHOICES = [
        ('customer_service', 'Customer Service'),
        ('information', 'Information'),
    ]
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='cms/', blank=True, null=True)
    in_footer = models.BooleanField(default=False)
    footer_section = models.CharField(
        max_length=20,
        choices=FOOTER_SECTION_CHOICES,
        blank=True,
        null=True,
        help_text='Select which footer section this page should appear in'
    )
    in_header = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'CMS Page'
        verbose_name_plural = 'CMS Pages'
        ordering = ['title']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title


class Order(models.Model):
    """Customer orders"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='billing_orders')
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='shipping_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"
    
    def calculate_total(self):
        """Calculate order total"""
        self.total = self.sub_total + self.shipping + self.tax
        return self.total


class OrderItem(models.Model):
    """Individual order line items"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    product_varient = models.CharField(max_length=255, blank=True, null=True)  # Store variant combination string
    earn_code = models.CharField(max_length=50, blank=True, null=True) # Check if used via referral
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    stock_deducted = models.BooleanField(default=False, help_text="Track if stock was deducted when order was delivered and paid")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['-created_at']
    
    def __str__(self):
        variant_str = f" - {self.product_varient}" if self.product_varient else ""
        return f"{self.order} - {self.product.name}{variant_str} - Qty: {self.quantity}"
    
    def save(self, *args, **kwargs):
        """Calculate total on save"""
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)


class Setting(models.Model):
    """Global system settings"""
    system_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sale_commision = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_withdrawal = models.BooleanField(default=True)
    min_withdrawal = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    max_withdrawal = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    low_stock_threshold = models.IntegerField(default=10, validators=[MinValueValidator(0)], help_text="Alert when product stock falls below this quantity")
    
    # Contact Information
    email = models.EmailField(blank=True, null=True, help_text="Contact email address")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Contact phone number")
    address = models.TextField(blank=True, null=True, help_text="Physical address")
    
    # Social Media Links
    facebook_url = models.URLField(blank=True, null=True, help_text="Facebook page URL")
    instagram_url = models.URLField(blank=True, null=True, help_text="Instagram profile URL")
    youtube_url = models.URLField(blank=True, null=True, help_text="YouTube channel URL")
    tiktok_url = models.URLField(blank=True, null=True, help_text="TikTok profile URL")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        
    def __str__(self):
        return "System Settings"


class Task(models.Model):
    """Admin created tasks"""
    SOCIAL_MEDIA_CHOICES = [
        ('youtube', 'Youtube'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
    ]
    
    social_media = models.CharField(max_length=20, choices=SOCIAL_MEDIA_CHOICES)
    title = models.CharField(max_length=255)
    target = models.CharField(max_length=255, help_text="Goal/Target for the task")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title


class UserTask(models.Model):
    """User attempts at tasks"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='user_submissions')
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reject_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Task'
        verbose_name_plural = 'User Tasks'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.task.title}"


class UserTaskImage(models.Model):
    """Image proofs for user tasks"""
    user_task = models.ForeignKey(UserTask, on_delete=models.CASCADE, related_name='images')
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='tasks/proofs/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Task Image'
        verbose_name_plural = 'User Task Images'


class UserTaskLink(models.Model):
    """Link proofs for user tasks"""
    user_task = models.ForeignKey(UserTask, on_delete=models.CASCADE, related_name='links')
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Task Link'
        verbose_name_plural = 'User Task Links'


class Withdrawal(models.Model):
    """User withdrawal requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    reject_reason = models.TextField(blank=True, null=True)
    
    screenshot_prove = models.ImageField(upload_to='withdrawals/proofs/', blank=True, null=True, help_text="Admin proof of payment")
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Withdrawal'
        verbose_name_plural = 'Withdrawals'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.amount}"


class Transaction(models.Model):
    """Ledger for balance changes"""
    TYPE_CHOICES = [
        ('in', 'In (Credit)'),
        ('out', 'Out (Debit)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"


class PasswordResetOTP(models.Model):
    """OTP for password reset"""
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    token = models.CharField(max_length=64, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Password Reset OTP'
        verbose_name_plural = 'Password Reset OTPs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_used']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.otp_code}"
    
    def is_expired(self):
        """Check if OTP has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()