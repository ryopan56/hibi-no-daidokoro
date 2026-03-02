from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image

from .models import MealLog, MealLogPhoto


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
