import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from .models import AiUsageLog
from .services.ai_client import AITimeoutError, AIClientError


class AiEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def _post_json(self, path, payload):
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_login_required(self):
        self.client.logout()
        response = self.client.post('/ai/minimum', data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    @patch('ai.views.OpenAIStructuredClient.suggest')
    def test_minimum_success(self, mock_suggest):
        mock_suggest.return_value = {
            'message': '提案しました',
            'suggestions': [
                {
                    'title': '卵雑炊',
                    'why': '短時間で作れます',
                    'estimated_time_minutes': 15,
                    'ingredients': ['卵', 'ごはん'],
                    'steps': ['煮る'],
                }
            ],
        }

        response = self._post_json('/ai/minimum', {'available_ingredients': ['卵']})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['mode'], 'minimum')
        self.assertEqual(len(data['suggestions']), 1)

        usage = AiUsageLog.objects.get()
        self.assertEqual(usage.mode, 'minimum')
        self.assertEqual(usage.status, 'ok')
        self.assertEqual(usage.jst_date, timezone.localdate())

    @patch('ai.views.OpenAIStructuredClient.suggest')
    def test_rate_limited_on_fourth_request(self, mock_suggest):
        today = timezone.localdate()
        for _ in range(3):
            AiUsageLog.objects.create(
                user=self.user,
                mode='minimum',
                jst_date=today,
                status='ok',
            )

        response = self._post_json('/ai/recommend', {'notes': 'test'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'rate_limited')
        self.assertEqual(data['mode'], 'recommend')
        self.assertEqual(
            data['message'],
            '本日のAI提案は上限（3回）に達しました。明日またお試しください。',
        )
        mock_suggest.assert_not_called()

        self.assertEqual(AiUsageLog.objects.count(), 4)
        latest = AiUsageLog.objects.order_by('-id').first()
        self.assertEqual(latest.status, 'rate_limited')

    @patch('ai.views.OpenAIStructuredClient.suggest')
    def test_api_error_fallback(self, mock_suggest):
        mock_suggest.side_effect = AIClientError('api error', error_type='api_error')

        response = self._post_json('/ai/recommend', {'notes': 'test'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'fallback')
        self.assertEqual(data['mode'], 'recommend')
        self.assertEqual(
            data['message'],
            '現在AI提案が混み合っています。代わりに簡易案を表示します。',
        )
        self.assertGreaterEqual(len(data['suggestions']), 2)

        usage = AiUsageLog.objects.get()
        self.assertEqual(usage.status, 'fallback')
        self.assertEqual(usage.error_type, 'api_error')

    @patch('ai.views.OpenAIStructuredClient.suggest')
    def test_timeout_fallback(self, mock_suggest):
        mock_suggest.side_effect = AITimeoutError()

        response = self._post_json('/ai/minimum', {'notes': 'test'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'fallback')
        self.assertEqual(data['mode'], 'minimum')
        usage = AiUsageLog.objects.get()
        self.assertEqual(usage.error_type, 'timeout')

    @patch('ai.views.OpenAIStructuredClient.suggest')
    def test_invalid_json_fallback_and_validation_log(self, mock_suggest):
        response = self.client.post(
            '/ai/minimum',
            data='{invalid json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'fallback')
        self.assertEqual(data['mode'], 'minimum')
        mock_suggest.assert_not_called()

        usage = AiUsageLog.objects.get()
        self.assertEqual(usage.status, 'fallback')
        self.assertEqual(usage.error_type, 'validation')

    @patch('django.utils.timezone.localdate')
    @patch('ai.views.OpenAIStructuredClient.suggest')
    def test_jst_date_is_saved_from_localdate(self, mock_suggest, mock_localdate):
        mock_localdate.return_value = date(2026, 3, 6)
        mock_suggest.return_value = {
            'message': 'ok',
            'suggestions': [
                {
                    'title': 'test',
                    'why': 'test',
                    'estimated_time_minutes': None,
                    'ingredients': [],
                    'steps': [],
                }
            ],
        }

        response = self._post_json('/ai/minimum', {})
        self.assertEqual(response.status_code, 200)
        usage = AiUsageLog.objects.get()
        self.assertEqual(usage.jst_date, date(2026, 3, 6))
