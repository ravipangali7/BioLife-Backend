"""
Stock management utility functions
"""
from django.db import transaction
from decimal import Decimal
from .models import Product


def deduct_stock(product, quantity, variant_combination=None, order_id=None, user=None, reason=None):
    """
    Deduct stock from product (main or variant)
    Returns: (success: bool, message: str)
    """
    try:
        with transaction.atomic():
            # Get current stock
            if variant_combination and product.product_varient:
                combinations = product.product_varient.get('combinations', {})
                if variant_combination in combinations:
                    previous_stock = combinations[variant_combination].get('stock', product.stock)
                    if previous_stock < quantity:
                        return False, f"Insufficient stock. Available: {previous_stock}, Requested: {quantity}"
                    
                    # Deduct from variant
                    combinations[variant_combination]['stock'] = previous_stock - quantity
                    product.product_varient['combinations'] = combinations
                    product.save(update_fields=['product_varient'])
                else:
                    # Variant doesn't exist, use main stock
                    previous_stock = product.stock
                    if previous_stock < quantity:
                        return False, f"Insufficient stock. Available: {previous_stock}, Requested: {quantity}"
                    
                    product.stock -= quantity
                    product.save(update_fields=['stock'])
            else:
                # Deduct from main stock
                previous_stock = product.stock
                if previous_stock < quantity:
                    return False, f"Insufficient stock. Available: {previous_stock}, Requested: {quantity}"
                
                product.stock -= quantity
                product.save(update_fields=['stock'])
            
            return True, "Stock deducted successfully"
            
    except Exception as e:
        return False, f"Error deducting stock: {str(e)}"


def add_stock(product, quantity, variant_combination=None, reason=None, user=None, reference=None, reference_type=None):
    """
    Add stock to product (main or variant)
    Returns: (success: bool, message: str)
    """
    try:
        with transaction.atomic():
            # Get current stock
            if variant_combination and product.product_varient:
                combinations = product.product_varient.get('combinations', {})
                if variant_combination in combinations:
                    previous_stock = combinations[variant_combination].get('stock', product.stock)
                    combinations[variant_combination]['stock'] = previous_stock + quantity
                    product.product_varient['combinations'] = combinations
                    product.save(update_fields=['product_varient'])
                else:
                    # Variant doesn't exist, use main stock
                    product.stock += quantity
                    product.save(update_fields=['stock'])
            else:
                # Add to main stock
                product.stock += quantity
                product.save(update_fields=['stock'])
            
            return True, "Stock added successfully"
            
    except Exception as e:
        return False, f"Error adding stock: {str(e)}"


def adjust_stock(product, new_stock, variant_combination=None, reason=None, user=None):
    """
    Adjust stock to a specific quantity
    Returns: (success: bool, message: str)
    """
    try:
        with transaction.atomic():
            # Get current stock
            if variant_combination and product.product_varient:
                combinations = product.product_varient.get('combinations', {})
                if variant_combination in combinations:
                    combinations[variant_combination]['stock'] = new_stock
                    product.product_varient['combinations'] = combinations
                    product.save(update_fields=['product_varient'])
                else:
                    product.stock = new_stock
                    product.save(update_fields=['stock'])
            else:
                product.stock = new_stock
                product.save(update_fields=['stock'])
            
            return True, "Stock adjusted successfully"
            
    except Exception as e:
        return False, f"Error adjusting stock: {str(e)}"


def validate_stock_availability(product, quantity, variant_combination=None):
    """
    Validate if sufficient stock is available
    Returns: (is_available: bool, available_quantity: int, message: str)
    """
    if variant_combination and product.product_varient:
        combinations = product.product_varient.get('combinations', {})
        if variant_combination in combinations:
            available = combinations[variant_combination].get('stock', product.stock)
        else:
            available = product.stock
    else:
        available = product.stock
    
    if available >= quantity:
        return True, available, "Stock available"
    else:
        return False, available, f"Insufficient stock. Available: {available}, Requested: {quantity}"
