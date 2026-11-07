import base64
import json
import urllib.request
import urllib.error
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import MpesaTransaction


def get_mpesa_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    if not consumer_key or not consumer_secret:
        raise ValueError('MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be set.')

    auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    credentials = f'{consumer_key}:{consumer_secret}'.encode('utf-8')
    encoded_credentials = base64.b64encode(credentials).decode('utf-8')

    request = urllib.request.Request(
        auth_url,
        headers={'Authorization': f'Basic {encoded_credentials}'},
        method='GET',
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode('utf-8'))

    if 'access_token' not in data:
        raise ValueError('M-Pesa access token request failed.')

    return data['access_token']


def generate_mpesa_timestamp():
    return datetime.now().strftime('%Y%m%d%H%M%S')


def generate_mpesa_password(shortcode, passkey, timestamp):
    raw = f'{shortcode}{passkey}{timestamp}'.encode('utf-8')
    return base64.b64encode(raw).decode('utf-8')


def checkout_page(request):
    return render(request, 'payment/checkout.html')


@require_http_methods(['GET', 'POST'])
def stk_push(request):
    if request.method == 'GET':
        return JsonResponse({
            'message': 'Use POST with phone_number and amount to initiate an M-Pesa STK Push.',
            'example': {
                'phone_number': '254712345678',
                'amount': 100,
                'account_reference': 'Order-001',
            }
        })

    if request.content_type == 'application/json':
        payload = json.loads(request.body or b'{}')
    else:
        payload = request.POST

    phone_number = str(payload.get('phone_number', '')).strip()
    amount = payload.get('amount', 0)
    account_reference = str(payload.get('account_reference', 'Order-001')).strip() or 'Order-001'
    transaction_desc = str(payload.get('transaction_desc', 'Order payment')).strip() or 'Order payment'

    if not phone_number or not amount:
        return JsonResponse({'error': 'phone_number and amount are required.'}, status=400)

    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    callback_url = settings.MPESA_CALLBACK_URL

    if not shortcode or not passkey:
        return JsonResponse({'error': 'MPESA_SHORTCODE and MPESA_PASSKEY must be configured.'}, status=500)

    timestamp = generate_mpesa_timestamp()
    password = generate_mpesa_password(shortcode, passkey, timestamp)

    try:
        access_token = get_mpesa_access_token()
    except (ValueError, urllib.error.URLError, OSError) as exc:
        return JsonResponse({'error': f'M-Pesa auth failed: {exc}'}, status=500)

    request_body = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': shortcode,
        'PhoneNumber': phone_number,
        'CallBackURL': callback_url,
        'AccountReference': account_reference,
        'TransactionDesc': transaction_desc,
    }

    transaction = MpesaTransaction.objects.create(
        phone_number=phone_number,
        amount=amount,
        account_reference=account_reference,
        transaction_desc=transaction_desc,
        status=MpesaTransaction.STATUS_PENDING,
    )

    stk_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    if settings.MPESA_ENV == 'production':
        stk_url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    data = json.dumps(request_body).encode('utf-8')
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    req = urllib.request.Request(stk_url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        error_message = exc.read().decode('utf-8', errors='ignore')
        transaction.status = MpesaTransaction.STATUS_FAILED
        transaction.result_desc = error_message
        transaction.save(update_fields=['status', 'result_desc', 'updated_at'])
        return JsonResponse({'error': 'M-Pesa STK Push request failed.', 'details': error_message}, status=500)
    except urllib.error.URLError as exc:
        transaction.status = MpesaTransaction.STATUS_FAILED
        transaction.result_desc = str(exc.reason)
        transaction.save(update_fields=['status', 'result_desc', 'updated_at'])
        return JsonResponse({'error': f'Could not reach M-Pesa: {exc.reason}'}, status=500)

    transaction.merchant_request_id = response_data.get('MerchantRequestID')
    transaction.checkout_request_id = response_data.get('CheckoutRequestID')
    transaction.result_code = response_data.get('ResponseCode')
    transaction.result_desc = response_data.get('ResponseDescription')
    if response_data.get('ResponseCode') == '0':
        transaction.status = MpesaTransaction.STATUS_PENDING
    else:
        transaction.status = MpesaTransaction.STATUS_FAILED
    transaction.save(update_fields=['merchant_request_id', 'checkout_request_id', 'result_code', 'result_desc', 'status', 'updated_at'])

    return JsonResponse(response_data)


@csrf_exempt
@require_http_methods(['POST'])
def mpesa_callback(request):
    try:
        callback_payload = json.loads(request.body.decode('utf-8'))
    except (TypeError, ValueError):
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid callback payload'}, status=400)

    # The callback is usually sent by Safaricom as a POST request with a nested stkCallback object.
    # Store/update your payment record here based on ResultCode and other metadata.
    body = callback_payload.get('Body', {})
    stk_callback = body.get('stkCallback', {})
    result_code = stk_callback.get('ResultCode')
    result_desc = stk_callback.get('ResultDesc', 'Callback received')
    checkout_request_id = stk_callback.get('CheckoutRequestID')

    transaction = None
    if checkout_request_id:
        transaction = MpesaTransaction.objects.filter(checkout_request_id=checkout_request_id).first()

    if transaction is not None:
        transaction.result_code = result_code
        transaction.result_desc = result_desc
        transaction.status = (
            MpesaTransaction.STATUS_SUCCESS if result_code == 0 else MpesaTransaction.STATUS_FAILED
        )
        transaction.save(update_fields=['result_code', 'result_desc', 'status', 'updated_at'])

    return JsonResponse({
        'ResultCode': 0,
        'ResultDesc': 'Accepted',
        'mpesa_result_code': result_code,
        'mpesa_result_desc': result_desc,
    })


