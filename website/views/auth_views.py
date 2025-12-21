from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.crypto import get_random_string
import secrets
from datetime import timedelta
from core.models import User, PasswordResetOTP


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
        account_type = request.POST.get('account_type', 'customer')
        
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
                is_influencer = (account_type == 'influencer')
                
                # Create user with basic info
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    password=password,
                    is_influencer=is_influencer,
                )
                
                # Save social media links if user is influencer
                if is_influencer:
                    tiktok_link = request.POST.get('tiktok_link', '').strip()
                    facebook_link = request.POST.get('facebook_link', '').strip()
                    youtube_link = request.POST.get('youtube_link', '').strip()
                    instagram_link = request.POST.get('instagram_link', '').strip()
                    
                    # Only save non-empty links
                    if tiktok_link:
                        user.tiktok_link = tiktok_link
                    if facebook_link:
                        user.facebook_link = facebook_link
                    if youtube_link:
                        user.youtube_link = youtube_link
                    if instagram_link:
                        user.instagram_link = instagram_link
                    
                    user.save()
                
                login(request, user)
                messages.success(request, f'Welcome to BioLife, {user.name}!')
                
                # Redirect influencers to profile to complete KYC
                if is_influencer:
                    messages.info(request, 'Please complete your KYC verification in your profile to access Earn Rewards and Wallet features.')
                    return redirect('website:account_profile')
                
                return redirect('website:home')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'site/auth/register.html')


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('website:home')


def forget_password_view(request):
    """Forget password - send OTP to email"""
    if request.user.is_authenticated:
        return redirect('website:home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Please enter your email address')
        else:
            # Check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Don't reveal if email exists for security
                messages.success(request, 'If an account exists with this email, an OTP has been sent.')
                return redirect('website:verify_otp')
            
            # Generate 6-digit OTP
            otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            
            # Generate secure token
            token = secrets.token_urlsafe(32)
            
            # Set expiration (15 minutes)
            expires_at = timezone.now() + timedelta(minutes=15)
            
            # Invalidate any existing OTPs for this email
            PasswordResetOTP.objects.filter(email=email, is_used=False).update(is_used=True)
            
            # Create new OTP
            otp_obj = PasswordResetOTP.objects.create(
                email=email,
                otp_code=otp_code,
                token=token,
                expires_at=expires_at
            )
            
            # Send email with OTP
            try:
                subject = 'BioLife - Password Reset OTP'
                
                # Get logo URL (absolute URL)
                logo_relative_path = staticfiles_storage.url('core/logo.png')
                logo_url = request.build_absolute_uri(logo_relative_path)
                
                # Render HTML email template
                html_content = render_to_string('emails/password_reset_otp.html', {
                    'user_name': user.name,
                    'otp_code': otp_code,
                    'logo_url': logo_url,
                })
                
                # Render plain text email template
                text_content = render_to_string('emails/password_reset_otp.txt', {
                    'user_name': user.name,
                    'otp_code': otp_code,
                })
                
                # Create email message with both HTML and plain text
                email_message = EmailMultiAlternatives(
                    subject,
                    text_content,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@biolife.com',
                    [email],
                )
                email_message.attach_alternative(html_content, "text/html")
                email_message.send(fail_silently=False)
                
                messages.success(request, 'OTP has been sent to your email address')
                # Store email in session for verification step
                request.session['reset_email'] = email
                return redirect('website:verify_otp')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
    
    return render(request, 'site/auth/forget_password.html')


def verify_otp_view(request):
    """Verify OTP code"""
    if request.user.is_authenticated:
        return redirect('website:home')
    
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Please start the password reset process')
        return redirect('website:forget_password')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        
        if not otp_code:
            messages.error(request, 'Please enter the OTP code')
        else:
            # Find valid OTP
            try:
                otp_obj = PasswordResetOTP.objects.filter(
                    email=email,
                    otp_code=otp_code,
                    is_used=False
                ).order_by('-created_at').first()
                
                if otp_obj and otp_obj.is_valid():
                    # Mark OTP as used
                    otp_obj.is_used = True
                    otp_obj.save()
                    
                    # Redirect to reset password with token
                    messages.success(request, 'OTP verified successfully')
                    return redirect('website:reset_password', token=otp_obj.token)
                else:
                    messages.error(request, 'Invalid or expired OTP code')
            except Exception as e:
                messages.error(request, 'Error verifying OTP')
    
    return render(request, 'site/auth/verify_otp.html', {'email': email})


def reset_password_view(request, token):
    """Reset password after OTP verification"""
    if request.user.is_authenticated:
        return redirect('website:home')
    
    # Find valid token
    try:
        otp_obj = PasswordResetOTP.objects.get(token=token, is_used=True)
    except PasswordResetOTP.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link')
        return redirect('website:forget_password')
    
    # Check if token is expired (additional check)
    if otp_obj.is_expired():
        messages.error(request, 'Reset link has expired. Please request a new one.')
        return redirect('website:forget_password')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        if not password or not password_confirm:
            messages.error(request, 'Please fill in all fields')
        elif password != password_confirm:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
        else:
            try:
                user = User.objects.get(email=otp_obj.email)
                user.set_password(password)
                user.save()
                
                # Invalidate all OTPs for this email
                PasswordResetOTP.objects.filter(email=otp_obj.email).update(is_used=True)
                
                messages.success(request, 'Password has been reset successfully. Please login with your new password.')
                return redirect('website:login')
            except User.DoesNotExist:
                messages.error(request, 'User not found')
            except Exception as e:
                messages.error(request, f'Error resetting password: {str(e)}')
    
    return render(request, 'site/auth/reset_password.html', {'email': otp_obj.email})
