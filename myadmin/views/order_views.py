from django.shortcuts import render, get_object_or_404, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from core.models import Order, OrderItem
from core.stock_utils import add_stock
from django.forms import modelform_factory
from django import forms


@superuser_required
def order_list(request):
    """List all orders"""
    orders = Order.objects.select_related('user', 'billing_address', 'shipping_address').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(user__email__icontains=search_query) |
            Q(user__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(order_status=status_filter)
    
    payment_filter = request.GET.get('payment')
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)
    
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
    }
    
    return render(request, 'admin/orders/list.html', context)


@superuser_required
def order_detail(request, pk):
    """Order detail view"""
    order = get_object_or_404(Order.objects.select_related(
        'user', 'billing_address', 'shipping_address'
    ), pk=pk)
    
    items = OrderItem.objects.filter(order=order).select_related('product', 'campaign')
    
    # Get referrer users for items with earn_code
    from core.models import User
    from decimal import Decimal
    earn_codes = [item.earn_code for item in items if item.earn_code]
    referrers = {}
    if earn_codes:
        referrer_users = User.objects.filter(earn_code__in=earn_codes, is_influencer=True)
        referrers = {user.earn_code: user for user in referrer_users}
    
    # Prepare items with reward calculations
    items_with_rewards = []
    for item in items:
        reward_amount = None
        if item.campaign and item.earn_code and order.order_status == 'delivered' and order.payment_status == 'paid':
            camp = item.campaign
            if camp.commission_type == 'percentage':
                reward_amount = (
                    Decimal(str(item.price)) * item.quantity
                    * (Decimal(str(camp.commission_value)) / Decimal('100'))
                )
            else:
                reward_amount = Decimal(str(camp.commission_value)) * item.quantity
        items_with_rewards.append({
            'item': item,
            'reward_amount': reward_amount,
        })
    
    context = {
        'order': order,
        'items': items,
        'items_with_rewards': items_with_rewards,
        'referrers': referrers,
    }
    
    return render(request, 'admin/orders/detail.html', context)


@superuser_required
def order_edit(request, pk):
    """Edit order"""
    order = get_object_or_404(Order, pk=pk)
    
    OrderForm = modelform_factory(
        Order,
        fields=['payment_status', 'order_status', 'payment_method', 'sub_total', 'shipping', 'total',
                'shipping_charge', 'billing_address', 'shipping_address'],
        widgets={
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'order_status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'sub_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
            'shipping_charge': forms.Select(attrs={'class': 'form-select'}),
            'billing_address': forms.Select(attrs={'class': 'form-select'}),
            'shipping_address': forms.Select(attrs={'class': 'form-select'}),
        }
    )
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            old_order_status = order.order_status
            old_payment_status = order.payment_status
            
            order = form.save()
            
            # Restore stock if order is cancelled
            if old_order_status != 'cancelled' and order.order_status == 'cancelled':
                with transaction.atomic():
                    order_items = OrderItem.objects.filter(order=order).select_related('product')
                    for item in order_items:
                        variant = item.product_varient if item.product_varient else None
                        success, message = add_stock(
                            product=item.product,
                            quantity=item.quantity,
                            variant_combination=variant,
                            reason=f"Order #{order.id} cancelled - stock restored",
                            user=request.user,
                            reference=str(order.id),
                            reference_type='order_cancellation'
                        )
                        if not success:
                            messages.warning(request, f"Stock restoration warning for {item.product.name}: {message}")
            
            messages.success(request, f'Order #{order.id} updated successfully.')
            return redirect('myadmin:order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
    
    return render(request, 'admin/orders/form.html', {'form': form, 'order': order})


@superuser_required
def order_delete(request, pk):
    """Delete order"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        order_id = order.id
        order.delete()
        messages.success(request, f'Order #{order_id} deleted successfully.')
        return redirect('myadmin:order_list')
    
    return render(request, 'admin/orders/delete.html', {'order': order})

