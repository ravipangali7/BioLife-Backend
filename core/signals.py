from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from decimal import Decimal
from .models import Order, OrderItem, User, Setting, Transaction
from .stock_utils import deduct_stock


@receiver(pre_save, sender=Order)
def process_commission_and_stock_on_order_status_change(sender, instance, **kwargs):
    """
    Process commissions and deduct stock when order status changes to 'delivered' and payment_status is 'paid'.
    This runs before save to check the previous state.
    """
    if instance.pk:  # Only for existing orders
        try:
            old_order = Order.objects.get(pk=instance.pk)
            # Check if order status changed to 'delivered' and payment_status is 'paid'
            if (old_order.order_status != 'delivered' and instance.order_status == 'delivered' and 
                instance.payment_status == 'paid'):
                # Process commissions for all order items with earn_code
                process_order_commissions(instance)
                # Deduct stock for all order items
                deduct_stock_for_delivered_order(instance)
        except Order.DoesNotExist:
            pass


def process_order_commissions(order):
    """
    Process commissions for all order items that have an earn_code.
    Prevents duplicate processing by checking existing transactions.
    """
    if order.order_status != 'delivered' or order.payment_status != 'paid':
        return
    
    setting = Setting.objects.first()
    if not setting or not setting.sale_commision:
        return
    
    commission_percent = Decimal(str(setting.sale_commision))
    
    # Get all order items with earn_code
    order_items = OrderItem.objects.filter(
        order=order,
        earn_code__isnull=False
    ).exclude(earn_code='')
    
    for order_item in order_items:
        # Check if commission already processed for this order item
        transaction_exists = Transaction.objects.filter(
            user__earn_code=order_item.earn_code,
            remarks__icontains=f'Commission for Order #{order.id}, Item #{order_item.id}'
        ).exists()
        
        if transaction_exists:
            continue  # Skip if already processed
        
        # Find the influencer by earn_code
        try:
            influencer = User.objects.get(earn_code=order_item.earn_code, is_influencer=True)
        except User.DoesNotExist:
            continue  # Skip if earn_code doesn't belong to a valid influencer
        
        # Calculate commission: order_item.price * (commission_percent / 100)
        # Note: order_item.price is already the unit price, so we use order_item.total
        commission_amount = Decimal(str(order_item.total)) * (commission_percent / Decimal('100'))
        
        if commission_amount > 0:
            with db_transaction.atomic():
                # Add commission to influencer's balance
                influencer.balance = Decimal(str(influencer.balance)) + commission_amount
                influencer.save()
                
                # Create transaction record
                Transaction.objects.create(
                    user=influencer,
                    amount=commission_amount,
                    transaction_type='in',
                    remarks=f'Commission for Order #{order.id}, Item #{order_item.id} - {order_item.product.name}',
                    status='success'
                )


def deduct_stock_for_delivered_order(order):
    """
    Deduct stock for all order items when order is delivered and paid.
    Prevents duplicate deduction by checking stock_deducted flag.
    """
    if order.order_status != 'delivered' or order.payment_status != 'paid':
        return
    
    # Get all order items that haven't had stock deducted yet
    order_items = OrderItem.objects.filter(
        order=order,
        stock_deducted=False
    ).select_related('product')
    
    for order_item in order_items:
        product = order_item.product
        variant_combination = order_item.product_varient if order_item.product_varient else None
        
        # Deduct stock using the utility function
        success, message = deduct_stock(
            product=product,
            quantity=order_item.quantity,
            variant_combination=variant_combination,
            order_id=order.id,
            user=order.user,
            reason=f'Order #{order.id} delivered and paid - Item #{order_item.id}'
        )
        
        if success:
            # Mark stock as deducted to prevent duplicate deduction
            order_item.stock_deducted = True
            order_item.save(update_fields=['stock_deducted'])
        else:
            # Log the error but don't fail the order update
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Failed to deduct stock for Order #{order.id}, Item #{order_item.id}: {message}')
