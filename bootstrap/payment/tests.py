from django.test import TestCase

# Create your tests here.


class PaymentTests(TestCase):
    def test_payment_page(self):
        response = self.client.get('/payment/stk-push/')
        self.assertEqual(response.status_code, 200)

    def test_payment_post(self):
        data = {
            'amount': 100,
            'phone_number': '254712345678',
            'account_reference': 'Order-001',
        }

        response = self.client.post('/payment/stk-push/', data, content_type='application/json')
        self.assertEqual(response.status_code, 200)


    def test_payment_post_missing_fields(self):
        data = {
            'amount': 100,
        }

        response = self.client.post('/payment/stk-push/', data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_payment_post_invalid_content_type(self):
        data = {
            'amount': 100,
            'phone_number': '254712345678',
            'account_reference': 'Order-001',
        }

        response = self.client.post('/payment/stk-push/', data)
        self.assertEqual(response.status_code, 200)