from django.db import models


class DashboardMetric(models.Model):
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    label = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}: {self.value}'


class SalesSummary(models.Model):
    month = models.CharField(max_length=20)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    orders = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['month']

    def __str__(self):
        return f'{self.month} - {self.revenue}'


class DashboardAlert(models.Model):
    ALERT_INFO = 'info'
    ALERT_WARNING = 'warning'
    ALERT_DANGER = 'danger'

    LEVEL_CHOICES = [
        (ALERT_INFO, 'Info'),
        (ALERT_WARNING, 'Warning'),
        (ALERT_DANGER, 'Danger'),
    ]

    title = models.CharField(max_length=150)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=ALERT_INFO)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


