from django.http import HttpResponse


def home(request):
    return HttpResponse('Ecommerce home page')
