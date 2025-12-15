from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from core.models import Brand, Product


def brand_list(request, brand_id):
    """Brand page - redirects to products page with brand filter"""
    brand = get_object_or_404(Brand, pk=brand_id)
    # Redirect to products page with brand filter
    return redirect(f'/products/?brand={brand_id}')
