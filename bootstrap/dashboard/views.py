from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render

from dashboard.models import DashboardAlert, DashboardMetric, SalesSummary
from ecommerce.models import Order
from payment.models import MpesaTransaction


def _safe_decimal(value):
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return Decimal('0')


def home_dashboard(request):
    total_transactions = MpesaTransaction.objects.count()
    successful_transactions = MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_SUCCESS).count()
    pending_transactions = MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_PENDING).count()
    failed_transactions = MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_FAILED).count()
    recent_transactions = MpesaTransaction.objects.order_by('-created_at')[:5]

    successful_amounts = MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_SUCCESS).values_list('amount', flat=True)
    total_revenue = sum(float(amount) for amount in successful_amounts)

    sales_summaries = SalesSummary.objects.all().order_by('month')
    if not sales_summaries:
        default_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        sales_summaries = [
            SalesSummary.objects.create(month=month, revenue=0, orders=0)
            for month in default_months
        ]

    monthly_sales = []
    for summary in sales_summaries:
        monthly_sales.append({
            'label': summary.month,
            'value': float(summary.revenue),
        })

    max_sales_value = max((item['value'] for item in monthly_sales), default=0)
    for item in monthly_sales:
        item['height'] = (item['value'] / max_sales_value * 100) if max_sales_value else 0

    dashboard_metrics = DashboardMetric.objects.all().order_by('-created_at')[:5]
    alerts = DashboardAlert.objects.all().order_by('-created_at')[:5]

    recent_orders = Order.objects.order_by('-created_at')[:5]
    recent_orders_payload = []
    for order in recent_orders:
        recent_orders_payload.append({
            'id': f'#{order.order_number}',
            'customer': order.customer_name,
            'item': order.item_name,
            'amount': order.total_amount,
            'date': order.created_at.strftime('%Y-%m-%d'),
            'status': order.status.title(),
        })

    order_revenue = Order.objects.filter(status__in=[Order.STATUS_PAID, Order.STATUS_SHIPPED]).aggregate(total=Sum('total_amount'))['total'] or 0
    order_revenue = _safe_decimal(order_revenue)
    target_revenue = Decimal('60000')
    target_progress = 0 if target_revenue == 0 else (order_revenue / target_revenue) * 100

    context = {
        'total_transactions': total_transactions,
        'successful_transactions': successful_transactions,
        'pending_transactions': pending_transactions,
        'failed_transactions': failed_transactions,
        'total_revenue': total_revenue,
        'monthly_sales': monthly_sales,
        'recent_transactions': recent_transactions,
        'recent_orders': recent_orders_payload,
        'dashboard_metrics': dashboard_metrics,
        'alerts': alerts,
        'order_revenue': order_revenue,
        'target_revenue': target_revenue,
        'target_progress': min(float(target_progress), 100),
    }
    return render(request, 'dashboard/home.html', context)

