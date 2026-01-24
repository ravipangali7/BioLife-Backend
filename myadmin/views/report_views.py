from django.shortcuts import render, redirect
from myadmin.decorators import superuser_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg, F, DecimalField
from django.db.models.functions import TruncDate, TruncMonth, TruncYear, Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from core.models import (
    Order, OrderItem, Product, User, Category, Setting,
    Withdrawal, Transaction
)
from django.http import HttpResponse
import csv
import json


@superuser_required
def reports_index(request):
    """Reports dashboard/landing page"""
    return render(request, 'admin/reports/reports_index.html')


@superuser_required
def sales_report(request):
    """Sales report with filters"""
    # Default date range: last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get date range from request
    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
        except:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
            end_date = timezone.make_aware(end_date)
            # Include the full end date
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except:
            pass
    
    # Base queryset
    orders = Order.objects.filter(created_at__range=[start_date, end_date])
    
    # Filters
    order_status = request.GET.get('order_status')
    if order_status:
        orders = orders.filter(order_status=order_status)
    
    payment_status = request.GET.get('payment_status')
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    
    category_id = request.GET.get('category')
    if category_id:
        orders = orders.filter(items__product__category_id=category_id).distinct()
    
    product_id = request.GET.get('product')
    if product_id:
        orders = orders.filter(items__product_id=product_id).distinct()
    
    # Grouping
    group_by = request.GET.get('group_by', 'day')
    
    # Calculate metrics
    total_sales = orders.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    total_orders = orders.count()
    average_order_value = total_sales / total_orders if total_orders > 0 else Decimal('0.00')
    
    # Get order items for product analysis
    order_items = OrderItem.objects.filter(order__in=orders).select_related('product', 'order')
    
    # Top products by revenue
    top_products = order_items.values('product__name', 'product__sku').annotate(
        total_revenue=Sum('total'),
        total_quantity=Sum('quantity'),
        order_count=Count('order', distinct=True)
    ).order_by('-total_revenue')[:10]
    
    # Sales by date (for chart)
    if group_by == 'day':
        sales_by_date = orders.extra(
            select={'date': "DATE(created_at)"}
        ).values('date').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('date')
    elif group_by == 'month':
        sales_by_date = orders.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('month')
    else:
        sales_by_date = []
    
    # Sales by category
    sales_by_category = order_items.values('product__category__name').annotate(
        total=Sum('total'),
        quantity=Sum('quantity')
    ).order_by('-total')
    
    # Export
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_sales_report_csv(orders, order_items)
    
    categories = Category.objects.order_by('order', 'name')
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'orders': orders.order_by('-created_at')[:100],  # Recent orders
        'total_sales': total_sales,
        'total_orders': total_orders,
        'average_order_value': average_order_value,
        'top_products': top_products,
        'sales_by_date': sales_by_date,
        'sales_by_category': sales_by_category,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'order_status': order_status,
        'payment_status': payment_status,
        'category_id': category_id,
        'product_id': product_id,
        'group_by': group_by,
        'categories': categories,
        'products': products,
    }
    
    return render(request, 'admin/reports/sales_report.html', context)


@superuser_required
def inventory_report(request):
    """Inventory status report"""
    # Get global low stock threshold from settings
    setting = Setting.objects.first()
    low_stock_threshold = setting.low_stock_threshold if setting else 10
    
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')
    
    # Filters
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    stock_status = request.GET.get('stock_status')
    if stock_status == 'in_stock':
        products = products.filter(stock__gt=0)
    elif stock_status == 'low_stock':
        products = products.filter(stock__gt=0, stock__lte=low_stock_threshold)
    elif stock_status == 'out_of_stock':
        products = products.filter(stock=0)
    
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Annotate products with stock value
    from django.db.models import F, FloatField
    from django.db.models.functions import Cast
    products = products.annotate(
        stock_value=Cast(F('regular_price') * F('stock'), FloatField())
    )
    
    # Calculate inventory value
    total_stock_value = Decimal('0.00')
    total_stock_quantity = 0
    for product in products:
        total_stock_value += Decimal(str(product.regular_price)) * product.stock
        total_stock_quantity += product.stock
    
    # Low stock products
    low_stock_products = products.filter(
        stock__gt=0,
        stock__lte=low_stock_threshold
    ).count()
    
    out_of_stock_products = products.filter(stock=0).count()
    
    # Pagination
    paginator = Paginator(products.order_by('name'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Export
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_inventory_report_csv(products)
    
    categories = Category.objects.order_by('order', 'name')
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'total_stock_value': total_stock_value,
        'total_stock_quantity': total_stock_quantity,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'category_id': category_id,
        'stock_status': stock_status,
        'search_query': search_query,
        'categories': categories,
    }
    
    return render(request, 'admin/reports/inventory_report.html', context)


@superuser_required
def product_performance_report(request):
    """Product sales performance report"""
    # Default date range: last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
        except:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
            end_date = timezone.make_aware(end_date)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except:
            pass
    
    # Get order items in date range
    order_items = OrderItem.objects.filter(
        order__created_at__range=[start_date, end_date],
        order__payment_status='paid'
    ).select_related('product', 'order')
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        order_items = order_items.filter(product__category_id=category_id)
    
    # Product performance metrics
    product_performance = order_items.values(
        'product__id',
        'product__name',
        'product__sku',
        'product__category__name',
        'product__stock'
    ).annotate(
        total_revenue=Sum('total'),
        total_quantity=Sum('quantity'),
        order_count=Count('order', distinct=True),
        average_price=Avg('price')
    ).order_by('-total_revenue')
    
    # Best selling products
    best_selling = product_performance[:20]
    
    # Worst selling products (products with orders but low revenue)
    worst_selling = product_performance.order_by('total_revenue')[:20]
    
    # Products with no sales
    products_with_sales = [p['product__id'] for p in product_performance]
    no_sales_products = Product.objects.filter(
        is_active=True
    ).exclude(id__in=products_with_sales).order_by('name')[:20]
    
    # Export
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_product_performance_csv(product_performance, start_date, end_date)
    
    categories = Category.objects.order_by('order', 'name')
    
    context = {
        'product_performance': product_performance[:50],
        'best_selling': best_selling,
        'worst_selling': worst_selling,
        'no_sales_products': no_sales_products,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'category_id': category_id,
        'categories': categories,
    }
    
    return render(request, 'admin/reports/product_performance.html', context)


@superuser_required
def customer_report(request):
    """Customer analytics report"""
    # Default date range: last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
        except:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
            end_date = timezone.make_aware(end_date)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except:
            pass
    
    # Get orders in date range
    orders = Order.objects.filter(created_at__range=[start_date, end_date])
    
    # Customer metrics
    customer_stats = orders.values(
        'user__id',
        'user__name',
        'user__email',
        'user__date_joined'
    ).annotate(
        total_spent=Sum('total'),
        order_count=Count('id'),
        average_order_value=Avg('total')
    ).order_by('-total_spent')
    
    # Top customers
    top_customers = customer_stats[:20]
    
    # New customers in period
    new_customers = User.objects.filter(
        date_joined__range=[start_date, end_date]
    ).count()
    
    # Total customers
    total_customers = User.objects.count()
    
    # Export
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_customer_report_csv(customer_stats, start_date, end_date)
    
    context = {
        'top_customers': top_customers,
        'new_customers': new_customers,
        'total_customers': total_customers,
        'customer_stats': customer_stats[:50],
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'admin/reports/customer_report.html', context)


# Export functions
def export_sales_report_csv(orders, order_items):
    """Export sales report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Date', 'Customer', 'Status', 'Payment Status', 'Total'])
    
    for order in orders:
        writer.writerow([
            order.id,
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            order.user.email,
            order.get_order_status_display(),
            order.get_payment_status_display(),
            order.total
        ])
    
    return response


def export_inventory_report_csv(products):
    """Export inventory report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
    
    writer = csv.writer(response)
    # Get global low stock threshold from settings
    setting = Setting.objects.first()
    low_stock_threshold = setting.low_stock_threshold if setting else 10
    
    writer.writerow(['SKU', 'Product Name', 'Category', 'Current Stock', 'Low Stock Threshold', 'Price', 'Stock Value', 'Status'])
    
    for product in products:
        status = 'Out of Stock' if product.stock == 0 else ('Low Stock' if product.is_low_stock() else 'In Stock')
        stock_value = float(product.regular_price) * product.stock
        writer.writerow([
            product.sku,
            product.name,
            product.category.name if product.category else '-',
            product.stock,
            low_stock_threshold,
            product.regular_price,
            stock_value,
            status
        ])
    
    return response


def export_product_performance_csv(product_performance, start_date, end_date):
    """Export product performance to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="product_performance_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['SKU', 'Product Name', 'Category', 'Total Revenue', 'Total Quantity', 'Orders', 'Average Price', 'Current Stock'])
    
    for item in product_performance:
        writer.writerow([
            item['product__sku'],
            item['product__name'],
            item['product__category__name'] or '-',
            item['total_revenue'] or 0,
            item['total_quantity'] or 0,
            item['order_count'] or 0,
            item['average_price'] or 0,
            item['product__stock'] or 0
        ])
    
    return response


def export_customer_report_csv(customer_stats, start_date, end_date):
    """Export customer report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="customer_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Customer Name', 'Email', 'Total Spent', 'Order Count', 'Average Order Value', 'Date Joined'])
    
    for stat in customer_stats:
        writer.writerow([
            stat['user__name'] or '-',
            stat['user__email'],
            stat['total_spent'] or 0,
            stat['order_count'] or 0,
            stat['average_order_value'] or 0,
            stat['user__date_joined'].strftime('%Y-%m-%d') if stat['user__date_joined'] else '-'
        ])
    
    return response


@superuser_required
def finance_report(request):
    """Finance report with withdrawals, transactions, and system balance"""
    # Default date range: last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get date range from request
    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
        except:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
            end_date = timezone.make_aware(end_date)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except:
            pass
    
    # Get system balance
    setting = Setting.objects.first()
    system_balance = setting.system_balance if setting else Decimal('0.00')
    
    # Base querysets
    withdrawals = Withdrawal.objects.filter(created_at__range=[start_date, end_date]).select_related('user')
    transactions = Transaction.objects.filter(created_at__range=[start_date, end_date]).select_related('user')
    
    # Filters
    withdrawal_status = request.GET.get('withdrawal_status')
    if withdrawal_status:
        withdrawals = withdrawals.filter(status=withdrawal_status)
    
    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    transaction_status = request.GET.get('transaction_status')
    if transaction_status:
        transactions = transactions.filter(status=transaction_status)
    
    # Withdrawal statistics
    total_withdrawals = withdrawals.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    withdrawals_by_status = withdrawals.values('status').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('status')
    
    withdrawals_by_payment_status = withdrawals.values('payment_status').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('payment_status')
    
    # Transaction statistics
    total_transactions_in = transactions.filter(transaction_type='in').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_transactions_out = transactions.filter(transaction_type='out').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    net_balance_flow = total_transactions_in - total_transactions_out
    
    transactions_by_type = transactions.values('transaction_type').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('transaction_type')
    
    # Commission tracking (from Transaction remarks containing "Commission")
    commissions = transactions.filter(remarks__icontains='Commission')
    total_commissions = commissions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    commission_count = commissions.count()
    
    # Grouping by date
    group_by = request.GET.get('group_by', 'day')
    if group_by == 'day':
        withdrawals_by_date = withdrawals.extra(
            select={'date': "DATE(created_at)"}
        ).values('date').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('date')
        
        transactions_by_date = transactions.extra(
            select={'date': "DATE(created_at)"}
        ).values('date').annotate(
            count=Count('id'),
            total_in=Sum('amount', filter=Q(transaction_type='in')),
            total_out=Sum('amount', filter=Q(transaction_type='out'))
        ).order_by('date')
    elif group_by == 'month':
        withdrawals_by_date = withdrawals.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('month')
        
        transactions_by_date = transactions.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_in=Sum('amount', filter=Q(transaction_type='in')),
            total_out=Sum('amount', filter=Q(transaction_type='out'))
        ).order_by('month')
    else:
        withdrawals_by_date = []
        transactions_by_date = []
    
    # Export
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_finance_report_csv(withdrawals, transactions, start_date, end_date)
    
    context = {
        'withdrawals': withdrawals.order_by('-created_at')[:100],
        'transactions': transactions.order_by('-created_at')[:100],
        'total_withdrawals': total_withdrawals,
        'withdrawals_by_status': withdrawals_by_status,
        'withdrawals_by_payment_status': withdrawals_by_payment_status,
        'total_transactions_in': total_transactions_in,
        'total_transactions_out': total_transactions_out,
        'net_balance_flow': net_balance_flow,
        'transactions_by_type': transactions_by_type,
        'total_commissions': total_commissions,
        'commission_count': commission_count,
        'system_balance': system_balance,
        'withdrawals_by_date': withdrawals_by_date,
        'transactions_by_date': transactions_by_date,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'withdrawal_status': withdrawal_status,
        'transaction_type': transaction_type,
        'transaction_status': transaction_status,
        'group_by': group_by,
    }
    
    return render(request, 'admin/reports/finance_report.html', context)


@superuser_required
def influencer_report(request):
    """Influencer performance report"""
    # Default date range: last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
        except:
            pass
    
    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
            end_date = timezone.make_aware(end_date)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except:
            pass
    
    # Base queryset - all influencers
    influencers = User.objects.filter(is_influencer=True)
    
    # Filters
    kyc_status = request.GET.get('kyc_status')
    if kyc_status:
        influencers = influencers.filter(kyc_status=kyc_status)
    
    # Get transactions in date range for earnings calculation
    transactions_in_range = Transaction.objects.filter(
        created_at__range=[start_date, end_date],
        transaction_type='in',
        status='success'
    )
    
    # Annotate influencers with metrics
    influencer_stats = influencers.annotate(
        total_earnings=Coalesce(
            Sum(
                'transactions__amount',
                filter=Q(
                    transactions__created_at__range=[start_date, end_date],
                    transactions__transaction_type='in',
                    transactions__status='success'
                )
            ),
            Decimal('0.00')
        ),
        commission_count=Count(
            'transactions',
            filter=Q(
                transactions__created_at__range=[start_date, end_date],
                transactions__remarks__icontains='Commission',
                transactions__status='success'
            )
        ),
        commission_earnings=Coalesce(
            Sum(
                'transactions__amount',
                filter=Q(
                    transactions__created_at__range=[start_date, end_date],
                    transactions__remarks__icontains='Commission',
                    transactions__status='success'
                )
            ),
            Decimal('0.00')
        ),
    ).order_by('-total_earnings')
    
    # Top influencers
    top_influencers = influencer_stats[:20]
    
    # KYC status distribution
    kyc_distribution = influencers.values('kyc_status').annotate(
        count=Count('id')
    ).order_by('kyc_status')
    
    # Total metrics
    total_influencers = influencers.count()
    total_earnings_all = influencer_stats.aggregate(
        total=Sum('total_earnings')
    )['total'] or Decimal('0.00')
    
    total_commissions = transactions_in_range.filter(remarks__icontains='Commission').count()
    
    # Average earnings per influencer
    avg_earnings = total_earnings_all / total_influencers if total_influencers > 0 else Decimal('0.00')
    
    # Export
    export_format = request.GET.get('export')
    if export_format == 'csv':
        return export_influencer_report_csv(influencer_stats, start_date, end_date)
    
    context = {
        'influencer_stats': influencer_stats[:50],
        'top_influencers': top_influencers,
        'kyc_distribution': kyc_distribution,
        'total_influencers': total_influencers,
        'total_earnings_all': total_earnings_all,
        'total_commissions': total_commissions,
        'avg_earnings': avg_earnings,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'kyc_status': kyc_status,
    }
    
    return render(request, 'admin/reports/influencer_report.html', context)


def export_finance_report_csv(withdrawals, transactions, start_date, end_date):
    """Export finance report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="finance_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Withdrawals section
    writer.writerow(['=== WITHDRAWALS ==='])
    writer.writerow(['ID', 'User', 'Amount', 'Status', 'Payment Status', 'Date'])
    for withdrawal in withdrawals:
        writer.writerow([
            withdrawal.id,
            withdrawal.user.email,
            withdrawal.amount,
            withdrawal.get_status_display(),
            withdrawal.get_payment_status_display(),
            withdrawal.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    writer.writerow([])
    
    # Transactions section
    writer.writerow(['=== TRANSACTIONS ==='])
    writer.writerow(['ID', 'User', 'Amount', 'Type', 'Status', 'Remarks', 'Date'])
    for transaction in transactions:
        writer.writerow([
            transaction.id,
            transaction.user.email,
            transaction.amount,
            transaction.get_transaction_type_display(),
            transaction.get_status_display(),
            transaction.remarks or '-',
            transaction.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    writer.writerow([])
    
    # Summary section
    total_withdrawals = withdrawals.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_in = transactions.filter(transaction_type='in').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_out = transactions.filter(transaction_type='out').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    writer.writerow(['=== SUMMARY ==='])
    writer.writerow(['Total Withdrawals', total_withdrawals])
    writer.writerow(['Total Transactions In', total_in])
    writer.writerow(['Total Transactions Out', total_out])
    writer.writerow(['Net Balance Flow', total_in - total_out])
    
    return response


def export_influencer_report_csv(influencer_stats, start_date, end_date):
    """Export influencer report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="influencer_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Influencers section
    writer.writerow(['=== INFLUENCERS ==='])
    writer.writerow(['Name', 'Email', 'Total Earnings', 'Commission Count', 'Commission Earnings', 'KYC Status'])
    for influencer in influencer_stats:
        writer.writerow([
            influencer.name or '-',
            influencer.email,
            influencer.total_earnings or 0,
            influencer.commission_count or 0,
            influencer.commission_earnings or 0,
            influencer.get_kyc_status_display() if influencer.kyc_status else 'Not Submitted'
        ])
    
    return response
