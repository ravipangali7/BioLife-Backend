from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from core.models import Order, OrderItem, Address, Coupon
from .cart_views import get_cart
from decimal import Decimal


@login_required(login_url='website:login')
def checkout(request):
    """Checkout page"""
    cart = get_cart(request)
    
    if not cart.get('items'):
        messages.warning(request, 'Your cart is empty')
        return redirect('website:cart')
    
    # Get user addresses
    addresses = Address.objects.filter(user=request.user)
    
    # Calculate cart totals (same logic as cart view)
    subtotal = Decimal('0.00')
    for item in cart['items']:
        from core.models import Product
        try:
            product = Product.objects.get(pk=item['product_id'], is_active=True)
            item_total = Decimal(str(item['price'])) * item['quantity']
            subtotal += item_total
        except Product.DoesNotExist:
            continue
    
    shipping = Decimal('0.00') if subtotal >= 50 else Decimal('5.00')
    tax = subtotal * Decimal('0.10')
    
    discount = Decimal('0.00')
    coupon = None
    if cart.get('coupon_code'):
        try:
            coupon = Coupon.objects.get(coupon_code=cart['coupon_code'])
            if coupon.is_valid():
                if coupon.discount_type == 'flat':
                    discount = coupon.discount
                else:
                    discount = subtotal * (coupon.discount / 100)
        except Coupon.DoesNotExist:
            pass
    
    total = subtotal + shipping + tax - discount
    
    if request.method == 'POST':
        billing_address_id = request.POST.get('billing_address')
        shipping_address_id = request.POST.get('shipping_address')
        use_same_address = request.POST.get('use_same_address') == 'on'
        
        try:
            billing_address = Address.objects.get(pk=billing_address_id, user=request.user)
            
            if use_same_address:
                shipping_address = billing_address
            else:
                shipping_address = Address.objects.get(pk=shipping_address_id, user=request.user)
            
            # Create order
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    billing_address=billing_address,
                    shipping_address=shipping_address,
                    sub_total=subtotal,
                    shipping=shipping,
                    tax=tax,
                    total=total,
                    payment_status='pending',
                    order_status='pending',
                )
                
                # Create order items
                for item in cart['items']:
                    from core.models import Product
                    try:
                        product = Product.objects.get(pk=item['product_id'], is_active=True)
                        price = Decimal(str(item['price']))
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_varient=item.get('variant', ''),
                            quantity=item['quantity'],
                            price=price,
                            total=price * item['quantity'],
                        )
                    except Product.DoesNotExist:
                        continue
                
                # Clear cart
                cart['items'] = []
                cart['coupon_code'] = None
                request.session.modified = True
                
                # Update coupon usage
                if coupon:
                    coupon.usage += 1
                    coupon.save()
            
            messages.success(request, 'Order placed successfully!')
            return redirect('website:checkout_success', order_id=order.id)
            
        except Address.DoesNotExist:
            messages.error(request, 'Please select valid addresses')
        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
    
    context = {
        'addresses': addresses,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'discount': discount,
        'total': total,
        'coupon': coupon,
    }
    
    return render(request, 'site/checkout/checkout.html', context)


@login_required
def checkout_success(request, order_id):
    """Order confirmation page"""
    try:
        order = Order.objects.get(pk=order_id, user=request.user)
        context = {
            'order': order,
        }
        return render(request, 'site/checkout/success.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('website:home')
