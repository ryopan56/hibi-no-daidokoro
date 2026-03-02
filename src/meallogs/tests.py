from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from .models import MealLog


class MealLogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def test_get_creates_log_once(self):
        target_date = date(2026, 3, 2)
        response = self.client.get(f"/logs/{target_date.isoformat()}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            MealLog.objects.filter(user=self.user, log_date=target_date).count(),
            1,
        )

        response = self.client.get(f"/logs/{target_date.isoformat()}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            MealLog.objects.filter(user=self.user, log_date=target_date).count(),
            1,
        )

    def test_post_updates(self):
        target_date = date(2026, 3, 2)
        response = self.client.post(
            f"/logs/{target_date.isoformat()}/",
            {
                "time_minutes": "30",
                "taste_level": "2",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        log = MealLog.objects.get(user=self.user, log_date=target_date)
        self.assertEqual(log.time_minutes, 30)
        self.assertEqual(log.taste_level, 2)

    def test_invalid_date_returns_404(self):
        response = self.client.get("/logs/2026-13-40/")
        self.assertEqual(response.status_code, 404)
