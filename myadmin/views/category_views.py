from django.shortcuts import render, get_object_or_404, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Category, SubCategory, ChildCategory
from django.forms import modelform_factory
from django import forms


# Category Views
@superuser_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.order_by('order', 'name')
    
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    paginator = Paginator(categories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'admin/categories/list.html', context)


@superuser_required
def category_detail(request, pk):
    """Category detail view"""
    category = get_object_or_404(Category, pk=pk)
    sub_categories = SubCategory.objects.filter(category=category)
    products = category.products.all()[:10]
    
    context = {
        'category': category,
        'sub_categories': sub_categories,
        'products': products,
    }
    
    return render(request, 'admin/categories/detail.html', context)


@superuser_required
def category_create(request):
    """Create new category"""
    CategoryForm = modelform_factory(
        Category,
        fields=['name', 'image', 'order', 'is_featured'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Auto-incremented if empty'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully.')
            return redirect('myadmin:category_detail', pk=category.pk)
    else:
        form = CategoryForm()
    
    return render(request, 'admin/categories/form.html', {'form': form})


@superuser_required
def category_edit(request, pk):
    """Edit category"""
    category = get_object_or_404(Category, pk=pk)
    
    CategoryForm = modelform_factory(
        Category,
        fields=['name', 'image', 'order', 'is_featured'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Auto-incremented if empty'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    )
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully.')
            return redirect('myadmin:category_detail', pk=category.pk)
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'admin/categories/form.html', {'form': form, 'category': category})


@superuser_required
def category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully.')
        return redirect('myadmin:category_list')
    
    return render(request, 'admin/categories/delete.html', {'category': category})


# SubCategory Views
@superuser_required
def subcategory_list(request):
    """List all subcategories"""
    subcategories = SubCategory.objects.select_related('category').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        subcategories = subcategories.filter(name__icontains=search_query)
    
    category_filter = request.GET.get('category')
    if category_filter:
        subcategories = subcategories.filter(category_id=category_filter)
    
    paginator = Paginator(subcategories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.order_by('order', 'name')
    
    context = {
        'page_obj': page_obj,
        'subcategories': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    
    return render(request, 'admin/subcategories/list.html', context)


@superuser_required
def subcategory_detail(request, pk):
    """SubCategory detail view"""
    subcategory = get_object_or_404(SubCategory.objects.select_related('category'), pk=pk)
    child_categories = ChildCategory.objects.filter(sub_category=subcategory)
    products = subcategory.products.all()[:10]
    
    context = {
        'subcategory': subcategory,
        'child_categories': child_categories,
        'products': products,
    }
    
    return render(request, 'admin/subcategories/detail.html', context)


@superuser_required
def subcategory_create(request):
    """Create new subcategory"""
    SubCategoryForm = modelform_factory(
        SubCategory,
        fields=['name', 'category', 'image'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'SubCategory "{subcategory.name}" created successfully.')
            return redirect('myadmin:subcategory_detail', pk=subcategory.pk)
    else:
        form = SubCategoryForm()
    
    categories = Category.objects.order_by('order', 'name')
    return render(request, 'admin/subcategories/form.html', {'form': form, 'categories': categories})


@superuser_required
def subcategory_edit(request, pk):
    """Edit subcategory"""
    subcategory = get_object_or_404(SubCategory, pk=pk)
    
    SubCategoryForm = modelform_factory(
        SubCategory,
        fields=['name', 'category', 'image'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, request.FILES, instance=subcategory)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'SubCategory "{subcategory.name}" updated successfully.')
            return redirect('myadmin:subcategory_detail', pk=subcategory.pk)
    else:
        form = SubCategoryForm(instance=subcategory)
    
    categories = Category.objects.order_by('order', 'name')
    return render(request, 'admin/subcategories/form.html', {'form': form, 'subcategory': subcategory, 'categories': categories})


@superuser_required
def subcategory_delete(request, pk):
    """Delete subcategory"""
    subcategory = get_object_or_404(SubCategory, pk=pk)
    
    if request.method == 'POST':
        subcategory_name = subcategory.name
        subcategory.delete()
        messages.success(request, f'SubCategory "{subcategory_name}" deleted successfully.')
        return redirect('myadmin:subcategory_list')
    
    return render(request, 'admin/subcategories/delete.html', {'subcategory': subcategory})


# ChildCategory Views
@superuser_required
def childcategory_list(request):
    """List all child categories"""
    childcategories = ChildCategory.objects.select_related('sub_category__category').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        childcategories = childcategories.filter(name__icontains=search_query)
    
    subcategory_filter = request.GET.get('subcategory')
    if subcategory_filter:
        childcategories = childcategories.filter(sub_category_id=subcategory_filter)
    
    paginator = Paginator(childcategories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    subcategories = SubCategory.objects.select_related('category').all()
    
    context = {
        'page_obj': page_obj,
        'childcategories': page_obj,
        'subcategories': subcategories,
        'search_query': search_query,
        'subcategory_filter': subcategory_filter,
    }
    
    return render(request, 'admin/childcategories/list.html', context)


@superuser_required
def childcategory_detail(request, pk):
    """ChildCategory detail view"""
    childcategory = get_object_or_404(ChildCategory.objects.select_related('sub_category__category'), pk=pk)
    products = childcategory.products.all()[:10]
    
    context = {
        'childcategory': childcategory,
        'products': products,
    }
    
    return render(request, 'admin/childcategories/detail.html', context)


@superuser_required
def childcategory_create(request):
    """Create new child category"""
    ChildCategoryForm = modelform_factory(
        ChildCategory,
        fields=['name', 'sub_category', 'image'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = ChildCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            childcategory = form.save()
            messages.success(request, f'ChildCategory "{childcategory.name}" created successfully.')
            return redirect('myadmin:childcategory_detail', pk=childcategory.pk)
    else:
        form = ChildCategoryForm()
    
    subcategories = SubCategory.objects.select_related('category').all()
    return render(request, 'admin/childcategories/form.html', {'form': form, 'subcategories': subcategories})


@superuser_required
def childcategory_edit(request, pk):
    """Edit child category"""
    childcategory = get_object_or_404(ChildCategory, pk=pk)
    
    ChildCategoryForm = modelform_factory(
        ChildCategory,
        fields=['name', 'sub_category', 'image'],
        widgets={
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    )
    
    if request.method == 'POST':
        form = ChildCategoryForm(request.POST, request.FILES, instance=childcategory)
        if form.is_valid():
            childcategory = form.save()
            messages.success(request, f'ChildCategory "{childcategory.name}" updated successfully.')
            return redirect('myadmin:childcategory_detail', pk=childcategory.pk)
    else:
        form = ChildCategoryForm(instance=childcategory)
    
    subcategories = SubCategory.objects.select_related('category').all()
    return render(request, 'admin/childcategories/form.html', {'form': form, 'childcategory': childcategory, 'subcategories': subcategories})


@superuser_required
def childcategory_delete(request, pk):
    """Delete child category"""
    childcategory = get_object_or_404(ChildCategory, pk=pk)
    
    if request.method == 'POST':
        childcategory_name = childcategory.name
        childcategory.delete()
        messages.success(request, f'ChildCategory "{childcategory_name}" deleted successfully.')
        return redirect('myadmin:childcategory_list')
    
    return render(request, 'admin/childcategories/delete.html', {'childcategory': childcategory})

