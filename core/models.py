from django.db import models
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
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email


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
    
    def get_final_price(self, variant_combination=None):
        """Calculate final price considering discount and variant"""
        if variant_combination and self.product_varient:
            combinations = self.product_varient.get('combinations', {})
            if variant_combination in combinations:
                base_price = float(combinations[variant_combination].get('price', self.regular_price))
            else:
                base_price = float(self.regular_price)
        else:
            base_price = float(self.regular_price)
        
        if self.discount_type == 'flat':
            final_price = base_price - float(self.discount)
        elif self.discount_type == 'percentage':
            final_price = base_price * (1 - float(self.discount) / 100)
        else:
            final_price = base_price
        
        return max(0, final_price)  # Ensure price is not negative
    
    def get_variant_stock(self, variant_combination=None):
        """Get stock for specific variant combination"""
        if variant_combination and self.product_varient:
            combinations = self.product_varient.get('combinations', {})
            if variant_combination in combinations:
                return combinations[variant_combination].get('stock', self.stock)
        return self.stock


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


class CMSPage(models.Model):
    """Content management system pages"""
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='cms/', blank=True, null=True)
    in_footer = models.BooleanField(default=False)
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
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
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
