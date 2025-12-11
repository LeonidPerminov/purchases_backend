from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import uuid


class RegisterThrottlingTestCase(APITestCase):
    """
    Тест проверяет, что для эндпоинта регистрации
    с throttle_scope='register' срабатывает ограничение частоты запросов.
    """

    def setUp(self):
        self.url = reverse('register')

    def _build_payload(self):
        """
        Собираем данные для регистрации.
        Email делаем уникальным на каждый запрос,
        чтобы не упираться в валидацию "пользователь уже существует".
        """
        unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"

        return {
            # ❗ ВАЖНО: подстрой поля под свой сериализатор/регистрацию
            "email": unique_email,
            "password": "StrongPassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_register_throttling(self):
        """
        Допустим, в settings.py задано:
        'register': '5/hour'

        Тогда первые 5 запросов не должны вернуть 429,
        а 6-й запрос должен вернуть 429 Too Many Requests.
        """
        # Делаем 5 "нормальных" запросов
        for _ in range(5):
            payload = self._build_payload()
            response = self.client.post(self.url, data=payload, format='json')
            self.assertNotEqual(
                response.status_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Throttling сработал раньше времени, статус {response.status_code}"
            )

        # 6-й запрос — должен попасть под ограничение
        payload = self._build_payload()
        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Ожидали 429 Too Many Requests при превышении лимита регистрации",
        )