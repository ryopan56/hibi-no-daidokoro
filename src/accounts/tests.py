from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from meallogs.models import MealLog

from .models import NotificationSettings
from .services.weekly_praise_trigger import current_week_start_jst
from .services.weekly_praise import WEEKLY_PRAISE_FALLBACK, WeeklyPraiseError


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


class NotificationSettingsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def test_notification_settings_get_and_post(self):
        response = self.client.get('/settings/notifications/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/settings/notifications/',
            {
                'notifications_enabled': 'on',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        settings_obj = NotificationSettings.objects.get(user=self.user)
        self.assertTrue(settings_obj.notifications_enabled)
        self.assertFalse(settings_obj.weekly_praise_enabled)

    @patch('accounts.services.weekly_praise_trigger.generate_weekly_praise')
    def test_weekly_praise_disabled_does_not_generate_or_show(self, mock_generate):
        NotificationSettings.objects.create(
            user=self.user,
            notifications_enabled=True,
            weekly_praise_enabled=False,
        )

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '今週の台所')
        mock_generate.assert_not_called()

    @patch('accounts.services.weekly_praise_trigger.current_week_start_jst')
    @patch('accounts.services.weekly_praise_trigger.generate_weekly_praise')
    def test_weekly_praise_shown_once_per_week(self, mock_generate, mock_week_start):
        current_week_start = date(2026, 3, 8)
        mock_week_start.return_value = current_week_start
        mock_generate.return_value = {
            'headline': '今週の台所',
            'message': '今週のメッセージ',
        }

        settings_obj = NotificationSettings.objects.create(
            user=self.user,
            notifications_enabled=True,
            weekly_praise_enabled=True,
            last_weekly_praise_shown_week_start=current_week_start - timedelta(days=7),
        )

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '今週のメッセージ')

        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.last_weekly_praise_shown_week_start, current_week_start)

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '今週のメッセージ')
        self.assertEqual(mock_generate.call_count, 1)

    @patch('accounts.services.weekly_praise_trigger.current_week_start_jst')
    @patch('accounts.services.weekly_praise_trigger.generate_weekly_praise')
    def test_weekly_praise_shown_even_if_notifications_disabled(self, mock_generate, mock_week_start):
        current_week_start = date(2026, 3, 8)
        mock_week_start.return_value = current_week_start
        mock_generate.return_value = {
            'headline': '今週の台所',
            'message': '通知OFFでも週次肯定',
        }

        NotificationSettings.objects.create(
            user=self.user,
            notifications_enabled=False,
            weekly_praise_enabled=True,
            last_weekly_praise_shown_week_start=current_week_start - timedelta(days=7),
        )

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '通知OFFでも週次肯定')
        self.assertEqual(mock_generate.call_count, 1)

    @patch('accounts.services.weekly_praise_trigger.current_week_start_jst')
    @patch('accounts.services.weekly_praise_trigger.generate_weekly_praise')
    def test_two_weeks_gap_still_shows_only_once_on_home(self, mock_generate, mock_week_start):
        current_week_start = date(2026, 3, 22)
        mock_week_start.return_value = current_week_start
        mock_generate.return_value = {
            'headline': '今週の台所',
            'message': '2週間後メッセージ',
        }

        settings_obj = NotificationSettings.objects.create(
            user=self.user,
            notifications_enabled=True,
            weekly_praise_enabled=True,
            last_weekly_praise_shown_week_start=current_week_start - timedelta(days=14),
        )

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2週間後メッセージ')

        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.last_weekly_praise_shown_week_start, current_week_start)

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '2週間後メッセージ')
        self.assertEqual(mock_generate.call_count, 1)

    @patch('accounts.services.weekly_praise_trigger.current_week_start_jst')
    @patch('accounts.services.weekly_praise_trigger.generate_weekly_praise')
    def test_weekly_praise_ai_error_fallback(self, mock_generate, mock_week_start):
        current_week_start = date(2026, 3, 8)
        mock_week_start.return_value = current_week_start
        mock_generate.side_effect = WeeklyPraiseError('api error')

        settings_obj = NotificationSettings.objects.create(
            user=self.user,
            notifications_enabled=True,
            weekly_praise_enabled=True,
            last_weekly_praise_shown_week_start=current_week_start - timedelta(days=7),
        )

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, WEEKLY_PRAISE_FALLBACK['message'])

        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.weekly_praise_status, NotificationSettings.PRAISE_STATUS_FALLBACK)


class WeeklyPraiseWeekStartTests(TestCase):
    @patch('accounts.services.weekly_praise_trigger.timezone.localdate')
    def test_week_start_on_sunday(self, mock_localdate):
        mock_localdate.return_value = date(2026, 3, 8)  # Sunday
        self.assertEqual(current_week_start_jst(), date(2026, 3, 8))

    @patch('accounts.services.weekly_praise_trigger.timezone.localdate')
    def test_week_start_on_monday(self, mock_localdate):
        mock_localdate.return_value = date(2026, 3, 9)  # Monday
        self.assertEqual(current_week_start_jst(), date(2026, 3, 8))


class UiFoundationTemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='foundation-user',
            password='pass12345',
        )

    def test_login_uses_auth_shell_with_signup_secondary_cta(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-startup-layer')
        self.assertContains(response, 'ログインする')
        self.assertContains(response, '初めての方はこちら')
        self.assertNotContains(response, 'Calendar')

    def test_home_shows_transient_area_recent_logs_and_bottom_nav(self):
        MealLog.objects.create(user=self.user, log_date=date(2026, 3, 18))
        MealLog.objects.create(user=self.user, log_date=date(2026, 3, 17))
        self.client.login(login_id='foundation-user', password='pass12345')

        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'temporary message area')
        self.assertContains(response, '日付ごとのログ一覧')
        self.assertContains(response, '2026.03.18')
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Calendar')
        self.assertContains(response, 'Search')
        self.assertContains(response, '設定ハブ')
