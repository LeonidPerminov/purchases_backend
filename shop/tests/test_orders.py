from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status

from shop.models import (
    Shop,
    Category,
    Product,
    ProductInfo,
    Order,
    OrderItem,
    Contact,
)


class OrderBasketTests(APITestCase):
    """
    Тесты для эндпоинтов корзины и подтверждения заказа.
    Покрывают часть логики OrderViewSet.basket и OrderViewSet.confirm.
    """

    def setUp(self):
        # создаём пользователя и сразу авторизуем его в API-клиенте
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)

        # базовые сущности для товара
        self.shop = Shop.objects.create(name="Test shop")
        self.category = Category.objects.create(name="Test category")
        self.product = Product.objects.create(
            name="Test product",
            category=self.category,
        )
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            model="Model X",
            quantity=10,
            price=1000,
            price_rrc=1200,
            external_id=1,  # число, не строка
        )

        # Имена маршрутов для extra-actions:
        # если OrderViewSet зарегистрирован через router.register(r'order', OrderViewSet),
        # то basename по умолчанию = "order", и action'ы называются:
        #   "order-basket" и "order-confirm".
        # Если у тебя в router явно указан basename="orders",
        # то нужно будет поменять на "orders-basket"/"orders-confirm".
        self.basket_url = reverse("order-basket")
        self.confirm_url = reverse("order-confirm")

    def test_get_empty_basket_creates_order(self):
        """
        GET /orders/basket/ для нового пользователя:
        должна создаться пустая корзина в состоянии 'basket'.
        """
        response = self.client.get(self.basket_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # в БД должна появиться корзина
        basket = Order.objects.get(user=self.user, status="basket")
        self.assertEqual(basket.ordered_items.count(), 0)

        # и она же должна вернуться в ответе
        self.assertEqual(response.data["id"], basket.id)
        self.assertEqual(response.data["status"], "basket")

    def test_post_basket_adds_items(self):
        """
        POST /orders/basket/ добавляет позиции в корзину.
        """
        payload = {
            "items": [
                {"product_info": self.product_info.id, "quantity": 2},
            ]
        }

        response = self.client.post(self.basket_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        basket = Order.objects.get(user=self.user, status="basket")
        item = OrderItem.objects.get(order=basket, product_info=self.product_info)
        self.assertEqual(item.quantity, 2)

    @patch("shop.views.send_order_emails")
    def test_confirm_turns_basket_into_order_and_calls_celery(self, mock_task):
        """
        POST /orders/confirm/:
        - меняет состояние корзины на 'new'
        - проставляет контакт
        - вызывает send_order_emails.delay(...)
        """

        # сначала создаём корзину с товаром
        basket, _ = Order.objects.get_or_create(user=self.user, status="basket")
        OrderItem.objects.create(
            order=basket,
            product_info=self.product_info,
            quantity=1,
        )

        # создаём контакт пользователя
        contact = Contact.objects.create(
            user=self.user,
        )

        payload = {"contact_id": contact.id}
        response = self.client.post(self.confirm_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        basket.refresh_from_db()
        self.assertEqual(basket.status, "new")
        self.assertEqual(basket.contact_id, contact.id)

        # проверяем, что Celery-задача была вызвана
        mock_task.delay.assert_called_once_with(
            order_id=basket.id,
            user_id=self.user.id,
        )