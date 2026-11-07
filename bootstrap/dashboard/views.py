from django.shortcuts import render

from payment.models import MpesaTransaction


def home_dashboard(request):
    total_transactions = MpesaTransaction.objects.count()
    successful_transactions = MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_SUCCESS).count()
    pending_transactions = MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_PENDING).count()
    failed_transactions = MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_FAILED).count()
    recent_transactions = MpesaTransaction.objects.order_by('-created_at')[:5]
    successful_amounts = MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_SUCCESS).values_list('amount', flat=True)
    total_revenue = sum(float(amount) for amount in successful_amounts)

    monthly_sales = [
        {'label': 'Jan', 'value': 0, 'height': 0},
        {'label': 'Feb', 'value': 0, 'height': 0},
        {'label': 'Mar', 'value': 0, 'height': 0},
        {'label': 'Apr', 'value': 0, 'height': 0},
        {'label': 'May', 'value': 0, 'height': 0},
        {'label': 'Jun', 'value': 0, 'height': 0},
    ]

    for transaction in MpesaTransaction.objects.filter(status=MpesaTransaction.STATUS_SUCCESS):
        month_index = transaction.created_at.month - 1
        if 0 <= month_index < len(monthly_sales):
            monthly_sales[month_index]['value'] += float(transaction.amount)

    max_sales_value = max((item['value'] for item in monthly_sales), default=0)
    if max_sales_value:
        for item in monthly_sales:
            item['height'] = (item['value'] / max_sales_value) * 100
    else:
        for item in monthly_sales:
            item['height'] = 0

    recent_orders = [
        {'id': '#1001', 'customer': 'Mary W.', 'item': 'Laptop Bag', 'amount': 2500, 'date': '2026-11-01', 'status': 'Paid'},
        {'id': '#1002', 'customer': 'John K.', 'item': 'Wireless Mouse', 'amount': 1500, 'date': '2026-11-03', 'status': 'Paid'},
        {'id': '#1003', 'customer': 'Asha N.', 'item': 'Bluetooth Speaker', 'amount': 3200, 'date': '2026-11-04', 'status': 'Pending'},
        {'id': '#1004', 'customer': 'Peter M.', 'item': 'Keyboard', 'amount': 1800, 'date': '2026-11-05', 'status': 'Paid'},
        {'id': '#1005', 'customer': 'Lucy T.', 'item': 'Office Chair', 'amount': 4800, 'date': '2026-11-06', 'status': 'Shipped'},
    ]

    context = {
        'total_transactions': total_transactions,
        'successful_transactions': successful_transactions,
        'pending_transactions': pending_transactions,
        'failed_transactions': failed_transactions,
        'total_revenue': total_revenue,
        'monthly_sales': monthly_sales,
        'recent_transactions': recent_transactions,
        'recent_orders': recent_orders,
    }
    return render(request, 'dashboard/home.html', context)

