from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from core.models import User


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('website:home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                messages.success(request, f'Welcome back, {user.name}!')
                return redirect('website:home')
            else:
                messages.error(request, 'Invalid email or password')
        else:
            messages.error(request, 'Please fill in all fields')
    
    return render(request, 'site/auth/login.html')


def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('website:home')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validation
        if not all([name, email, password, password_confirm]):
            messages.error(request, 'Please fill in all fields')
        elif password != password_confirm:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
        else:
            try:
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    password=password,
                )
                login(request, user)
                messages.success(request, f'Welcome to BioLife, {user.name}!')
                return redirect('website:home')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'site/auth/register.html')


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('website:home')
