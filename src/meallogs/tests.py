from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import Client, TestCase, override_settings
from PIL import Image

from django.db import IntegrityError

from .enums import IngredientCategory
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
