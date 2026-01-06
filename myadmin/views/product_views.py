from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Product, ProductImage, ProductReview, Category, SubCategory, ChildCategory, Brand, Unit
from django.forms import modelform_factory, inlineformset_factory
from django import forms
import json


@login_required
def product_list(request):
    """List all products with search and filters"""
    products = Product.objects.select_related('category', 'brand', 'unit').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Filters
    category_filter = request.GET.get('category')
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    brand_filter = request.GET.get('brand')
    if brand_filter:
        products = products.filter(brand_id=brand_filter)
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    
    featured_filter = request.GET.get('featured')
    if featured_filter == 'yes':
        products = products.filter(is_featured=True)
    elif featured_filter == 'no':
        products = products.filter(is_featured=False)
    
    # Stock status filter
    from core.models import Setting
    setting = Setting.objects.first()
    low_stock_threshold = setting.low_stock_threshold if setting else 10
    
    stock_status_filter = request.GET.get('stock_status')
    if stock_status_filter == 'out_of_stock':
        products = products.filter(stock=0)
    elif stock_status_filter == 'low_stock':
        products = products.filter(stock__gt=0, stock__lte=low_stock_threshold)
    elif stock_status_filter == 'in_stock':
        products = products.filter(stock__gt=low_stock_threshold)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'categories': categories,
        'brands': brands,
        'search_query': search_query,
        'category_filter': category_filter,
        'brand_filter': brand_filter,
        'status_filter': status_filter,
        'featured_filter': featured_filter,
        'stock_status_filter': stock_status_filter,
    }
    
    return render(request, 'admin/products/list.html', context)


@login_required
def product_detail(request, pk):
    """Product detail view"""
    product = get_object_or_404(Product.objects.select_related(
        'category', 'sub_category', 'child_category', 'brand', 'unit'
    ), pk=pk)
    
    # Get related images
    images = ProductImage.objects.filter(product=product)
    
    # Get reviews
    reviews = ProductReview.objects.filter(product=product).select_related('user')
    
    context = {
        'product': product,
        'images': images,
        'reviews': reviews,
    }
    
    return render(request, 'admin/products/detail.html', context)


@login_required
def product_create(request):
    """Create new product"""
    ProductForm = modelform_factory(
        Product,
        fields=['name', 'sku', 'category', 'sub_category', 'child_category', 'brand', 'unit',
                'short_description', 'long_description', 'regular_price', 'stock',
                'discount_type', 'discount', 'is_active', 'is_featured', 'image', 'product_varient'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sub_category': forms.Select(attrs={'class': 'form-select'}),
            'child_category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'long_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'regular_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'product_varient': forms.HiddenInput(),
        }
    )
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle product_varient JSON string
            if 'product_varient' in request.POST:
                variant_data = request.POST.get('product_varient', '{}')
                try:
                    # Parse JSON string to dict for JSONField
                    variant_dict = json.loads(variant_data) if variant_data else {}
                    form.instance.product_varient = variant_dict
                    
                    # Validate that exactly one is_primary is selected when variants enabled
                    if variant_dict.get('enabled', False):
                        combinations = variant_dict.get('combinations', {})
                        primary_count = sum(
                            1 for combo in combinations.values() 
                            if isinstance(combo, dict) and combo.get('is_primary', False)
                        )
                        if primary_count != 1:
                            messages.error(request, 'Exactly one variant combination must be marked as primary.')
                            form.add_error(None, 'Primary variant validation failed.')
                            # Re-render form with error
                        else:
                            # Calculate stock and price from variants (will be done in model save)
                            pass
                except (json.JSONDecodeError, ValueError):
                    form.instance.product_varient = {}
            
            if form.is_valid():  # Check again after variant validation
                product = form.save()
                messages.success(request, f'Product "{product.name}" created successfully.')
                return redirect('myadmin:product_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all().select_related('category')
    childcategories = ChildCategory.objects.all().select_related('sub_category', 'sub_category__category')
    brands = Brand.objects.all()
    units = Unit.objects.all()
    
    # Serialize category data for JavaScript
    categories_data = [{'id': cat.id, 'name': cat.name} for cat in categories]
    subcategories_data = [{'id': sub.id, 'name': sub.name, 'category_id': sub.category.id} for sub in subcategories]
    childcategories_data = [{'id': child.id, 'name': child.name, 'subcategory_id': child.sub_category.id} for child in childcategories]
    
    # Get selected values for edit mode
    selected_data = {}
    if hasattr(form, 'instance') and form.instance.pk:
        if form.instance.category:
            selected_data['category'] = form.instance.category.id
        if form.instance.sub_category:
            selected_data['sub_category'] = form.instance.sub_category.id
        if form.instance.child_category:
            selected_data['child_category'] = form.instance.child_category.id
    
    context = {
        'form': form,
        'categories': categories,
        'brands': brands,
        'units': units,
        'categories_json': json.dumps(categories_data),
        'subcategories_json': json.dumps(subcategories_data),
        'childcategories_json': json.dumps(childcategories_data),
        'selected_json': json.dumps(selected_data),
        'variant_json': '{}',  # Empty for create mode
    }
    
    return render(request, 'admin/products/form.html', context)


@login_required
def product_edit(request, pk):
    """Edit product"""
    product = get_object_or_404(Product, pk=pk)
    
    ProductForm = modelform_factory(
        Product,
        fields=['name', 'sku', 'category', 'sub_category', 'child_category', 'brand', 'unit',
                'short_description', 'long_description', 'regular_price', 'stock',
                'discount_type', 'discount', 'is_active', 'is_featured', 'image', 'product_varient'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sub_category': forms.Select(attrs={'class': 'form-select'}),
            'child_category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'long_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'regular_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'product_varient': forms.HiddenInput(),
        }
    )
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # Handle product_varient JSON string
            if 'product_varient' in request.POST:
                variant_data = request.POST.get('product_varient', '{}')
                try:
                    # Parse JSON string to dict for JSONField
                    variant_dict = json.loads(variant_data) if variant_data else {}
                    form.instance.product_varient = variant_dict
                    
                    # Validate that exactly one is_primary is selected when variants enabled
                    if variant_dict.get('enabled', False):
                        combinations = variant_dict.get('combinations', {})
                        primary_count = sum(
                            1 for combo in combinations.values() 
                            if isinstance(combo, dict) and combo.get('is_primary', False)
                        )
                        if primary_count != 1:
                            messages.error(request, 'Exactly one variant combination must be marked as primary.')
                            form.add_error(None, 'Primary variant validation failed.')
                            # Re-render form with error
                        else:
                            # Calculate stock and price from variants (will be done in model save)
                            pass
                except (json.JSONDecodeError, ValueError):
                    form.instance.product_varient = {}
            
            if form.is_valid():  # Check again after variant validation
                product = form.save()
                messages.success(request, f'Product "{product.name}" updated successfully.')
                return redirect('myadmin:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all().select_related('category')
    childcategories = ChildCategory.objects.all().select_related('sub_category', 'sub_category__category')
    brands = Brand.objects.all()
    units = Unit.objects.all()
    
    # Serialize category data for JavaScript
    categories_data = [{'id': cat.id, 'name': cat.name} for cat in categories]
    subcategories_data = [{'id': sub.id, 'name': sub.name, 'category_id': sub.category.id} for sub in subcategories]
    childcategories_data = [{'id': child.id, 'name': child.name, 'subcategory_id': child.sub_category.id} for child in childcategories]
    
    # Get selected values for edit mode
    selected_data = {}
    if product.category:
        selected_data['category'] = product.category.id
    if product.sub_category:
        selected_data['sub_category'] = product.sub_category.id
    if product.child_category:
        selected_data['child_category'] = product.child_category.id
    
    # Serialize product variant data for JavaScript (if editing)
    variant_json = '{}'
    if product.product_varient:
        variant_json = json.dumps(product.product_varient)
    
    context = {
        'form': form,
        'product': product,
        'categories': categories,
        'brands': brands,
        'units': units,
        'categories_json': json.dumps(categories_data),
        'subcategories_json': json.dumps(subcategories_data),
        'childcategories_json': json.dumps(childcategories_data),
        'selected_json': json.dumps(selected_data),
        'variant_json': variant_json,
    }
    
    return render(request, 'admin/products/form.html', context)


@login_required
def product_delete(request, pk):
    """Delete product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully.')
        return redirect('myadmin:product_list')
    
    return render(request, 'admin/products/delete.html', {'product': product})


@login_required
def product_image_list(request, product_pk):
    """List product images"""
    product = get_object_or_404(Product, pk=product_pk)
    images = ProductImage.objects.filter(product=product)
    
    context = {
        'product': product,
        'images': images,
    }
    
    return render(request, 'admin/products/image_list.html', context)


@login_required
def product_review_list(request, product_pk):
    """List product reviews"""
    product = get_object_or_404(Product, pk=product_pk)
    reviews = ProductReview.objects.filter(product=product).select_related('user')
    
    context = {
        'product': product,
        'reviews': reviews,
    }
    
    return render(request, 'admin/products/review_list.html', context)

