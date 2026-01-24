from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from decimal import Decimal
from .models import Order, OrderItem, User, Transaction
from .stock_utils import deduct_stock


@receiver(pre_save, sender=Order)
def process_stock_on_order_status_change(sender, instance, **kwargs):
    """
    Deduct stock when order status changes to 'delivered' and payment_status is 'paid'.
    This runs before save to check the previous state.
    """
    if instance.pk:  # Only for existing orders
        try:
            old_order = Order.objects.get(pk=instance.pk)
            # Check if order status changed to 'delivered' and payment_status is 'paid'
            if (old_order.order_status != 'delivered' and instance.order_status == 'delivered' and 
                instance.payment_status == 'paid'):
                # Process campaign rewards
                process_campaign_rewards(instance)
                # Deduct stock for all order items
                deduct_stock_for_delivered_order(instance)
        except Order.DoesNotExist:
            pass


def process_campaign_rewards(order):
    """
    Process campaign rewards for all order items that have a campaign and earn_code.
    Prevents duplicate processing by checking existing transactions.
    """
    if order.order_status != 'delivered' or order.payment_status != 'paid':
        return
    
    # Get all order items with campaign and earn_code
    order_items = OrderItem.objects.filter(
        order=order,
        campaign__isnull=False,
        earn_code__isnull=False
    ).exclude(earn_code='').select_related('campaign', 'product')
    
    for order_item in order_items:
        # Check if reward already processed for this order item
        transaction_exists = Transaction.objects.filter(
            user__earn_code=order_item.earn_code,
            remarks__icontains=f'Campaign reward for Order #{order.id}, Item #{order_item.id}'
        ).exists()
        
        if transaction_exists:
            continue  # Skip if already processed
        
        # Find the referrer by earn_code
        try:
            referrer = User.objects.get(earn_code=order_item.earn_code, is_influencer=True, kyc_status='approved')
        except User.DoesNotExist:
            continue  # Skip if earn_code doesn't belong to a valid IBO
        
        # Calculate reward: order_item.price * (campaign.percentage / 100)
        # Note: order_item.price is the unit price
        reward_amount = Decimal(str(order_item.price)) * (Decimal(str(order_item.campaign.percentage)) / Decimal('100'))
        
        if reward_amount > 0:
            with db_transaction.atomic():
                # Add reward to referrer's balance
                referrer.balance = Decimal(str(referrer.balance)) + reward_amount
                referrer.save()
                
                # Create transaction record
                Transaction.objects.create(
                    user=referrer,
                    amount=reward_amount,
                    transaction_type='in',
                    remarks=f'Campaign reward for Order #{order.id}, Item #{order_item.id} - {order_item.product.name} (Campaign: {order_item.campaign.name}, {order_item.campaign.percentage}%)',
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
