from django.shortcuts import render


def home_dashboard(request):
    return render(request, 'dashboard.html')

