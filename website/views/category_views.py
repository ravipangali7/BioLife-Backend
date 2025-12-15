from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import Http404
from core.models import Category, SubCategory, Product


def category_list(request, category_id=None):
    """Category page - redirects to products page with category filter"""
    if category_id:
        category = get_object_or_404(Category, pk=category_id)
        # Redirect to products page with category filter
        return redirect(f'/products/?category={category_id}')
    else:
        # If no category_id, redirect to products page
        return redirect('website:product_list')


def subcategory_list(request, category_id, subcategory_id):
    """Subcategory page - redirects to products page with category filter"""
    category = get_object_or_404(Category, pk=category_id)
    subcategory = get_object_or_404(SubCategory, pk=subcategory_id, category=category)
    # Redirect to products page with category filter (parent category)
    return redirect(f'/products/?category={category_id}')
