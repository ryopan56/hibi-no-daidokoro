from datetime import date
from io import BytesIO
import json
import tempfile
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import Client, TestCase, override_settings
from PIL import Image

from django.db import IntegrityError

from .enums import IngredientCategory, TasteLevel
from .models import MealLog, MealLogIngredient, MealLogPhoto, MealLogTag, Tag


def make_test_image(name='test.png'):
    buffer = BytesIO()
    image = Image.new('RGB', (10, 10), color='blue')
    image.save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT='/tmp/test_media')
class MealLogPhotoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def test_upload_and_limit(self):
        target_date = date(2026, 3, 2)
        url = f"/logs/{target_date.isoformat()}/photos"

        files = [make_test_image(f"img_{i}.png") for i in range(3)]
        response = self.client.post(url, {"photos": files}, follow=True)
        self.assertEqual(response.status_code, 200)
        log = MealLog.objects.get(user=self.user, log_date=target_date)
        self.assertEqual(log.photos.count(), 3)

        more_files = [make_test_image(f"img_{i}.png") for i in range(10)]
        response = self.client.post(url, {"photos": more_files}, follow=True)
        self.assertEqual(response.status_code, 200)
        log.refresh_from_db()
        self.assertEqual(log.photos.count(), 3)

    def test_delete_ownership(self):
        target_date = date(2026, 3, 2)
        log = MealLog.objects.create(user=self.user, log_date=target_date)
        photo = MealLogPhoto.objects.create(meal_log=log, image=make_test_image())

        other = get_user_model().objects.create_user(
            login_id='other',
            password='pass12345',
        )
        other_log = MealLog.objects.create(user=other, log_date=target_date)
        other_photo = MealLogPhoto.objects.create(meal_log=other_log, image=make_test_image())

        response = self.client.post(f"/photos/{other_photo.id}/delete")
        self.assertEqual(response.status_code, 404)

        response = self.client.post(f"/photos/{photo.id}/delete", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MealLogPhoto.objects.filter(id=photo.id).exists())


class MealLogTagTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def test_add_delete_tag(self):
        target_date = date(2026, 3, 2)
        add_url = f"/logs/{target_date.isoformat()}/tags/add"

        response = self.client.post(add_url, {"tag_kind": "general", "tag_name": "朝食"}, follow=True)
        self.assertEqual(response.status_code, 200)
        log = MealLog.objects.get(user=self.user, log_date=target_date)
        self.assertEqual(log.tags.count(), 1)

        response = self.client.post(add_url, {"tag_kind": "general", "tag_name": "朝食"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(log.tags.count(), 1)

        tag = Tag.objects.get(kind="general", name="朝食")
        delete_url = f"/logs/{target_date.isoformat()}/tags/{tag.id}/delete"
        response = self.client.post(delete_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(log.tags.count(), 0)

    def test_delete_other_users_tag(self):
        target_date = date(2026, 3, 2)
        other = get_user_model().objects.create_user(
            login_id='other',
            password='pass12345',
        )
        other_log = MealLog.objects.create(user=other, log_date=target_date)
        tag = Tag.objects.create(kind='general', name='昼食')
        MealLogTag.objects.create(meal_log=other_log, tag=tag)

        delete_url = f"/logs/{target_date.isoformat()}/tags/{tag.id}/delete"
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 404)

    def test_candidates(self):
        target_date = date(2026, 3, 2)
        log = MealLog.objects.create(user=self.user, log_date=target_date)
        tag = Tag.objects.create(kind='general', name='夕食')
        MealLogTag.objects.create(meal_log=log, tag=tag)

        response = self.client.get(f"/logs/{target_date.isoformat()}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '夕食')


class MealLogIngredientTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def test_unique_constraint(self):
        target_date = date(2026, 3, 2)
        log = MealLog.objects.create(user=self.user, log_date=target_date)
        MealLogIngredient.objects.create(
            meal_log=log,
            category=IngredientCategory.MEAT.value,
        )
        with self.assertRaises(IntegrityError):
            MealLogIngredient.objects.create(
                meal_log=log,
                category=IngredientCategory.MEAT.value,
            )

    def test_save_update_categories(self):
        target_date = date(2026, 3, 2)
        url = f"/logs/{target_date.isoformat()}/"

        response = self.client.post(
            url,
            {
                "time_minutes": "",
                "taste_level": "",
                "ingredient_categories": [
                    str(IngredientCategory.MEAT.value),
                    str(IngredientCategory.VEGETABLE.value),
                ],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        log = MealLog.objects.get(user=self.user, log_date=target_date)
        self.assertEqual(
            set(log.ingredients.values_list("category", flat=True)),
            {IngredientCategory.MEAT.value, IngredientCategory.VEGETABLE.value},
        )

        response = self.client.post(
            url,
            {
                "time_minutes": "",
                "taste_level": "",
                "ingredient_categories": [
                    str(IngredientCategory.FISH.value),
                ],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        log.refresh_from_db()
        self.assertEqual(
            set(log.ingredients.values_list("category", flat=True)),
            {IngredientCategory.FISH.value},
        )

        response = self.client.post(
            url,
            {
                "time_minutes": "",
                "taste_level": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        log.refresh_from_db()
        self.assertEqual(log.ingredients.count(), 0)

    def test_other_users_log_not_affected(self):
        target_date = date(2026, 3, 2)
        other = get_user_model().objects.create_user(
            login_id='other',
            password='pass12345',
        )
        other_log = MealLog.objects.create(user=other, log_date=target_date)
        MealLogIngredient.objects.create(
            meal_log=other_log,
            category=IngredientCategory.BEAN.value,
        )

        response = self.client.post(
            f"/logs/{target_date.isoformat()}/",
            {
                "time_minutes": "",
                "taste_level": "",
                "ingredient_categories": [str(IngredientCategory.MEAT.value)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        other_log.refresh_from_db()
        self.assertEqual(
            set(other_log.ingredients.values_list("category", flat=True)),
            {IngredientCategory.BEAN.value},
        )


class MealLogSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.other_user = get_user_model().objects.create_user(
            login_id='other',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get("/search")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_and_search_and_date_link(self):
        hit_log = MealLog.objects.create(user=self.user, log_date=date(2026, 3, 3))
        breakfast_tag, _ = Tag.objects.get_or_create(kind='general', name='朝食')
        quick_tag, _ = Tag.objects.get_or_create(kind='general', name='時短')
        hit_log.tags.add(breakfast_tag, quick_tag)

        miss_log = MealLog.objects.create(user=self.user, log_date=date(2026, 3, 2))
        miss_log.tags.add(breakfast_tag)

        response = self.client.post(
            "/search",
            {"q": "朝食 時短"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026-03-03")
        self.assertNotContains(response, "2026-03-02")
        self.assertContains(
            response,
            reverse("meallog_detail", kwargs={"log_date": "2026-03-03"}),
        )

    def test_date_range_filters(self):
        MealLog.objects.create(user=self.user, log_date=date(2026, 3, 1))
        MealLog.objects.create(user=self.user, log_date=date(2026, 3, 5))
        MealLog.objects.create(user=self.user, log_date=date(2026, 3, 10))

        response = self.client.post(
            "/search",
            {"date_from": "2026-03-02", "date_to": "2026-03-08"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026-03-05")
        self.assertNotContains(response, "2026-03-01")
        self.assertNotContains(response, "2026-03-10")

    def test_from_greater_than_to_shows_error(self):
        response = self.client.post(
            "/search",
            {"date_from": "2026-03-10", "date_to": "2026-03-01"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "開始日以降の日付を指定してください。")

    def test_search_only_own_logs(self):
        own_log = MealLog.objects.create(user=self.user, log_date=date(2026, 3, 8))
        dinner_tag, _ = Tag.objects.get_or_create(kind='general', name='夕食')
        own_log.tags.add(dinner_tag)

        other_log = MealLog.objects.create(user=self.other_user, log_date=date(2026, 3, 9))
        other_log.tags.add(dinner_tag)

        response = self.client.post(
            "/search",
            {"q": "夕食"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026-03-08")
        self.assertNotContains(response, "2026-03-09")


class MealLogCalendarTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.other_user = get_user_model().objects.create_user(
            login_id='other',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get("/calendar/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_show_month_and_mark_only_own_logged_days(self):
        MealLog.objects.create(user=self.user, log_date=date(2026, 3, 3))
        MealLog.objects.create(user=self.user, log_date=date(2026, 3, 15))
        MealLog.objects.create(user=self.other_user, log_date=date(2026, 3, 9))

        response = self.client.get("/calendar/?year=2026&month=3")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026年3月")
        self.assertContains(
            response,
            reverse("meallog_detail", kwargs={"log_date": "2026-03-03"}),
        )
        self.assertContains(
            response,
            reverse("meallog_detail", kwargs={"log_date": "2026-03-15"}),
        )
        self.assertContains(response, "●", count=2)

    def test_invalid_year_month_fallback_to_today(self):
        with patch("meallogs.views.date") as mock_date:
            mock_date.today.return_value = date(2026, 4, 10)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

            response = self.client.get("/calendar/?year=invalid&month=99")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026年4月")


class MealLogBackupTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_root.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media_root.cleanup)

        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='tester',
            password='pass12345',
        )
        self.other_user = get_user_model().objects.create_user(
            login_id='other',
            password='pass12345',
        )
        self.client.login(login_id='tester', password='pass12345')

    def _build_backup_upload(self, payload, photo_files=None, include_photos_dir=False):
        photo_files = photo_files or {}
        buffer = BytesIO()
        with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as archive:
            archive.writestr('logs.json', json.dumps(payload, ensure_ascii=False))
            if include_photos_dir:
                archive.writestr('photos/', b'')
            for path, content in photo_files.items():
                archive.writestr(path, content)
        return SimpleUploadedFile(
            'backup.zip',
            buffer.getvalue(),
            content_type='application/zip',
        )

    def test_export_backup_zip_contains_schema_conform_logs_json(self):
        log = MealLog.objects.create(
            user=self.user,
            log_date=date(2026, 3, 2),
            time_minutes=30,
            taste_level=TasteLevel.from_code('HIGH'),
        )
        MealLogIngredient.objects.create(
            meal_log=log,
            category=IngredientCategory.MEAT.value,
        )
        MealLogIngredient.objects.create(
            meal_log=log,
            category=IngredientCategory.VEGETABLE.value,
        )
        breakfast_tag = Tag.objects.create(kind='general', name='朝食')
        quick_tag = Tag.objects.create(kind='general', name='時短')
        MealLogTag.objects.create(meal_log=log, tag=breakfast_tag)
        MealLogTag.objects.create(meal_log=log, tag=quick_tag)
        MealLogPhoto.objects.create(meal_log=log, image=make_test_image('breakfast.png'))

        response = self.client.post(reverse('meallog_export'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn(
            'attachment; filename="hibi-no-daidokoro-backup-',
            response['Content-Disposition'],
        )

        with ZipFile(BytesIO(response.content)) as archive:
            self.assertIn('logs.json', archive.namelist())
            self.assertTrue(any(name.startswith('photos/') for name in archive.namelist()))
            payload = json.loads(archive.read('logs.json').decode('utf-8'))

        self.assertEqual(payload['version'], 1)
        self.assertEqual(len(payload['logs']), 1)

        exported_log = payload['logs'][0]
        self.assertEqual(
            set(exported_log.keys()),
            {
                'log_date',
                'time_minutes',
                'taste_level',
                'ingredient_categories',
                'tags',
                'photos',
            },
        )
        self.assertEqual(exported_log['log_date'], '2026-03-02')
        self.assertEqual(exported_log['time_minutes'], 30)
        self.assertEqual(exported_log['taste_level'], 'HIGH')
        self.assertEqual(exported_log['ingredient_categories'], ['MEAT', 'VEGETABLE'])
        self.assertEqual(
            exported_log['tags'],
            [
                {'kind': 'general', 'name': '時短'},
                {'kind': 'general', 'name': '朝食'},
            ],
        )
        self.assertEqual(len(exported_log['photos']), 1)
        self.assertRegex(exported_log['photos'][0]['path'], r'^photos/2026-03-02/[^/]+$')

    def test_import_backup_overwrites_existing_logs_and_restores_photo_without_dir_entry(self):
        old_log = MealLog.objects.create(
            user=self.user,
            log_date=date(2026, 3, 10),
            time_minutes=10,
        )
        old_photo = MealLogPhoto.objects.create(
            meal_log=old_log,
            image=make_test_image('old.png'),
        )
        old_file_name = old_photo.image.name

        payload = {
            'version': 1,
            'logs': [
                {
                    'log_date': '2026-03-02',
                    'time_minutes': 45,
                    'taste_level': 'MEDIUM',
                    'ingredient_categories': ['FISH', 'BEAN'],
                    'tags': [
                        {'kind': 'general', 'name': '夕食'},
                    ],
                    'photos': [
                        {'path': 'photos/2026-03-02/restored.png'},
                    ],
                }
            ],
        }
        upload = self._build_backup_upload(
            payload,
            photo_files={
                'photos/2026-03-02/restored.png': make_test_image('restored.png').read(),
            },
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('meallog_import'),
                {'backup_file': upload},
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'バックアップを復元しました。')
        self.assertFalse(
            MealLog.objects.filter(user=self.user, log_date=date(2026, 3, 10)).exists()
        )

        restored_log = MealLog.objects.get(user=self.user, log_date=date(2026, 3, 2))
        self.assertEqual(restored_log.time_minutes, 45)
        self.assertEqual(restored_log.taste_level, TasteLevel.from_code('MEDIUM'))
        self.assertEqual(
            set(restored_log.ingredients.values_list('category', flat=True)),
            {IngredientCategory.FISH.value, IngredientCategory.BEAN.value},
        )
        self.assertEqual(
            list(restored_log.tags.values_list('kind', 'name')),
            [('general', '夕食')],
        )
        self.assertEqual(restored_log.photos.count(), 1)
        self.assertTrue(default_storage.exists(restored_log.photos.get().image.name))
        self.assertFalse(default_storage.exists(old_file_name))

    def test_import_backup_restores_photo_with_photos_dir_entry(self):
        payload = {
            'version': 1,
            'logs': [
                {
                    'log_date': '2026-03-03',
                    'time_minutes': 20,
                    'taste_level': 'LOW',
                    'ingredient_categories': [],
                    'tags': [],
                    'photos': [
                        {'path': 'photos/2026-03-03/with-dir.png'},
                    ],
                }
            ],
        }
        upload = self._build_backup_upload(
            payload,
            photo_files={
                'photos/2026-03-03/with-dir.png': make_test_image('with-dir.png').read(),
            },
            include_photos_dir=True,
        )

        response = self.client.post(
            reverse('meallog_import'),
            {'backup_file': upload},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'バックアップを復元しました。')
        restored_log = MealLog.objects.get(user=self.user, log_date=date(2026, 3, 3))
        self.assertEqual(restored_log.photos.count(), 1)

    def test_import_backup_rejects_invalid_schema_and_paths(self):
        invalid_cases = [
            (
                {
                    'version': 1,
                    'logs': [
                        {
                            'log_date': '2026-03-02',
                            'time_minutes': 10,
                            'taste_level': None,
                            'ingredient_categories': [],
                            'photos': [],
                        }
                    ],
                },
                {},
                'ログ項目に想定外の項目があります。',
            ),
            (
                {
                    'version': 1,
                    'logs': [
                        {
                            'log_date': '2026-03-02',
                            'time_minutes': 10,
                            'taste_level': None,
                            'ingredient_categories': [],
                            'tags': [],
                            'photos': [
                                {'path': '../evil.txt'},
                            ],
                        }
                    ],
                },
                {},
                'ZIP 内のパスが不正です。',
            ),
            (
                {
                    'version': 1,
                    'logs': [
                        {
                            'log_date': '2026-03-02',
                            'time_minutes': 10,
                            'taste_level': None,
                            'ingredient_categories': [],
                            'tags': [],
                            'photos': [
                                {'path': 'images/evil.png'},
                            ],
                        }
                    ],
                },
                {},
                'ZIP 内の構造が不正です。',
            ),
        ]

        for payload, photo_files, message in invalid_cases:
            with self.subTest(message=message):
                upload = self._build_backup_upload(
                    payload,
                    photo_files=photo_files,
                    include_photos_dir=True,
                )
                response = self.client.post(reverse('meallog_import'), {'backup_file': upload})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, message)

    def test_import_backup_rejects_unexpected_top_level_file(self):
        payload = {
            'version': 1,
            'logs': [],
        }
        buffer = BytesIO()
        with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as archive:
            archive.writestr('logs.json', json.dumps(payload))
            archive.writestr('photos/', b'')
            archive.writestr('extra.txt', b'bad')
        upload = SimpleUploadedFile(
            'backup.zip',
            buffer.getvalue(),
            content_type='application/zip',
        )

        response = self.client.post(reverse('meallog_import'), {'backup_file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ZIP 内に想定外のファイルがあります。')


class UiFoundationNavigationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            login_id='nav-user',
            password='pass12345',
        )
        self.client.login(login_id='nav-user', password='pass12345')

    def test_search_page_uses_shared_shell(self):
        response = self.client.get('/search/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '過去ログ検索')
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Calendar')
        self.assertContains(response, 'Search')
        self.assertContains(response, '設定ハブ')

    def test_calendar_page_uses_shared_shell(self):
        response = self.client.get('/calendar/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'カレンダー')
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Calendar')
        self.assertContains(response, 'Search')
