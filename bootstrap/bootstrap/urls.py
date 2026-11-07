from django.contrib import admin
from django.urls import path,include



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ecommerce.urls')),
    path('crm/', include('crm.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('payment/', include('payment.urls')),
]
