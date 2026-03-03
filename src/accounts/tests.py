from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_login_logout_flow(self):
        response = self.client.post(
            '/signup/',
            {
                'login_id': 'testuser',
                'password1': 'testpass123',
                'password2': 'testpass123',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(get_user_model().objects.filter(login_id='testuser').exists())

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/logout/', follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('/login/', response.redirect_chain[-1][0])
