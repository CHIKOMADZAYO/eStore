from django.urls import path

from .views import checkout_page, mpesa_callback, stk_push

urlpatterns = [
    path('', checkout_page, name='payment_checkout'),
    path('stk-push/', stk_push, name='stk_push'),
    path('callback/', mpesa_callback, name='mpesa_callback'),
]
