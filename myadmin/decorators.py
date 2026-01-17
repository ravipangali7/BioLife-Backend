from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def superuser_required(view_func):
    """Decorator that requires user to be authenticated and a superuser"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('website:login')
        if not request.user.is_superuser:
            messages.error(request, 'Access denied. Superuser privileges required.')
            return redirect('website:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
