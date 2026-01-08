from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from core.models import Product, Coupon
from decimal import Decimal


def get_cart(request):
    """Get or initialize cart from session"""
    if 'cart' not in request.session:
        request.session['cart'] = {
            'items': [],
            'coupon_code': None,
        }
    return request.session['cart']


def cart_view(request):
    """Display shopping cart"""
    cart = get_cart(request)
    cart_items = []
    subtotal = Decimal('0.00')
    
    for item in cart['items']:
        try:
            product = Product.objects.get(pk=item['product_id'], is_active=True)
            item_total = Decimal(str(item['price'])) * item['quantity']
            subtotal += item_total
            
            cart_items.append({
                'product': product,
                'variant': item.get('variant', ''),
                'quantity': item['quantity'],
                'price': Decimal(str(item['price'])),
                'total': item_total,
            })
        except Product.DoesNotExist:
            continue
    
    # Calculate shipping (free shipping over $50, otherwise $5)
    shipping = Decimal('0.00') if subtotal >= 50 else Decimal('5.00')
    
    # Tax removed from system
    tax = Decimal('0.00')
    
    # Apply coupon if exists
    discount = Decimal('0.00')
    coupon = None
    if cart.get('coupon_code'):
        try:
            coupon = Coupon.objects.get(coupon_code=cart['coupon_code'])
            if coupon.is_valid():
                if coupon.discount_type == 'flat':
                    discount = coupon.discount
                else:  # percentage
                    discount = subtotal * (coupon.discount / 100)
            else:
                cart['coupon_code'] = None
                request.session.modified = True
        except Coupon.DoesNotExist:
            cart['coupon_code'] = None
            request.session.modified = True
    
    total = subtotal + shipping - discount
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'discount': discount,
        'total': total,
        'coupon': coupon,
        'coupon_code': cart.get('coupon_code', ''),
    }
    
    return render(request, 'site/cart/cart.html', context)


def add_to_cart(request, product_id):
    """Add product to cart"""
    if request.method == 'POST':
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
            variant = request.POST.get('variant', '')
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity < 1:
                messages.error(request, 'Quantity must be at least 1')
                return redirect('website:product_detail', pk=product_id)
            
            # Check if product has variants enabled
            has_variants = product.product_varient and product.product_varient.get('enabled', False)
            
            # If product has variants but no variant provided, use is_primary variant
            if has_variants and not variant:
                combinations = product.product_varient.get('combinations', {})
                for combo_key, combo_data in combinations.items():
                    if isinstance(combo_data, dict) and combo_data.get('is_primary', False):
                        variant = combo_key
                        break
                
                # If still no variant found, return error
                if not variant:
                    messages.error(request, 'Please select a variant for this product')
                    return redirect('website:product_detail', pk=product_id)
            
            # Validate variant selection for products with variants
            if has_variants and not variant:
                messages.error(request, 'Variant selection is required for this product')
                return redirect('website:product_detail', pk=product_id)
            
            # Check stock
            if variant:
                stock = product.get_variant_stock(variant)
            else:
                stock = product.stock
            
            if quantity > stock:
                messages.error(request, f'Only {stock} items available in stock')
                return redirect('website:product_detail', pk=product_id)
            
            # Get price
            price = float(product.get_final_price(variant))
            
            cart = get_cart(request)
            
            # Get earn_code from session if available (from affiliate link)
            earn_code = request.session.get('affiliate_earn_code', '')
            
            # Check if item already exists
            item_found = False
            for item in cart['items']:
                if item['product_id'] == product_id and item.get('variant') == variant:
                    item['quantity'] += quantity
                    # Preserve existing earn_code or set new one if not present
                    if not item.get('earn_code') and earn_code:
                        item['earn_code'] = earn_code
                    item_found = True
                    break
            
            if not item_found:
                cart['items'].append({
                    'product_id': product_id,
                    'variant': variant,
                    'quantity': quantity,
                    'price': price,
                    'earn_code': earn_code,
                })
            
            request.session.modified = True
            messages.success(request, 'Product added to cart')
            
        except Product.DoesNotExist:
            messages.error(request, 'Product not found')
        except ValueError:
            messages.error(request, 'Invalid quantity')
    
    return redirect('website:cart')


def update_cart(request, item_index):
    """Update cart item quantity"""
    if request.method == 'POST':
        cart = get_cart(request)
        quantity = int(request.POST.get('quantity', 1))
        
        if 0 <= item_index < len(cart['items']):
            if quantity <= 0:
                cart['items'].pop(item_index)
            else:
                cart['items'][item_index]['quantity'] = quantity
            request.session.modified = True
            messages.success(request, 'Cart updated')
    
    return redirect('website:cart')


def remove_from_cart(request, item_index):
    """Remove item from cart"""
    cart = get_cart(request)
    if 0 <= item_index < len(cart['items']):
        cart['items'].pop(item_index)
        request.session.modified = True
        messages.success(request, 'Item removed from cart')
    
    return redirect('website:cart')


def apply_coupon(request):
    """Apply coupon code to cart"""
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '').strip().upper()
        cart = get_cart(request)
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(coupon_code=coupon_code)
                if coupon.is_valid():
                    cart['coupon_code'] = coupon_code
                    request.session.modified = True
                    messages.success(request, 'Coupon applied successfully')
                else:
                    messages.error(request, 'Coupon is not valid or has expired')
            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid coupon code')
        else:
            cart['coupon_code'] = None
            request.session.modified = True
            messages.success(request, 'Coupon removed')
    
    return redirect('website:cart')
