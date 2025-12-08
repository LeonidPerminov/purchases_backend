from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail

from rest_framework import viewsets, permissions, generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import ListAPIView

from .models import (
    Shop,
    Category,
    Product,
    Order,
    Contact,
    ProductInfo,
    OrderItem,
)
from .serializers import (
    ShopSerializer,
    CategorySerializer,
    ProductSerializer,
    OrderSerializer,
    OrderItemSerializer,
    ContactSerializer,
    RegisterSerializer,
    ProductInfoSerializer,
)

class ShopViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()   # ← ДОБАВИТЬ ЭТО

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-dt')

    def perform_create(self, serializer):
        # user проставляем автоматически
        serializer.save(user=self.request.user)

    # ---------- КОРЗИНА ----------

    @action(detail=False, methods=['get', 'post', 'delete'], url_path='basket')
    def basket(self, request, *args, **kwargs):
        """
        Корзина текущего пользователя.

        GET    /api/v1/orders/basket/   — получить корзину
        POST   /api/v1/orders/basket/   — добавить/изменить позиции
        DELETE /api/v1/orders/basket/   — удалить позиции
        """
        user = request.user

        # Получаем или создаём заказ в статусе 'basket'
        basket, _ = Order.objects.get_or_create(
            user=user,
            state='basket',
        )

        # ---------- GET: показать корзину ----------
        if request.method == 'GET':
            serializer = OrderSerializer(basket)
            return Response(serializer.data)

        # ---------- POST: добавить / обновить позиции ----------
        if request.method == 'POST':
            """
            Ожидаемый формат JSON:
            {
              "items": [
                {"product_info": 1, "quantity": 2},
                {"product_info": 5, "quantity": 1}
              ]
            }
            """
            items_data = request.data.get('items', [])
            if not isinstance(items_data, list) or not items_data:
                return Response(
                    {'error': 'Поле "items" должно быть непустым списком.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for item in items_data:
                product_info_id = item.get('product_info')
                quantity = int(item.get('quantity', 1))

                if not product_info_id:
                    return Response(
                        {'error': 'Для каждой позиции нужно указать "product_info".'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                try:
                    product_info = ProductInfo.objects.get(id=product_info_id)
                except ProductInfo.DoesNotExist:
                    return Response(
                        {'error': f'ProductInfo с id={product_info_id} не найден.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if quantity <= 0:
                    # 0 или меньше — удаляем позицию
                    OrderItem.objects.filter(
                        order=basket,
                        product_info=product_info
                    ).delete()
                    continue

                # создаём или обновляем позицию
                order_item, created = OrderItem.objects.get_or_create(
                    order=basket,
                    product_info=product_info,
                    defaults={'quantity': quantity},
                )
                if not created and order_item.quantity != quantity:
                    order_item.quantity = quantity
                    order_item.save()

            basket.refresh_from_db()
            serializer = OrderSerializer(basket)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # ---------- DELETE: удалить позиции ----------
        if request.method == 'DELETE':
            """
            Ожидаемый формат JSON:
            {
              "items": [1, 5, 10]   # id ProductInfo, которые нужно удалить из корзины
            }
            """
            items_ids = request.data.get('items', [])
            if not isinstance(items_ids, list) or not items_ids:
                return Response(
                    {'error': 'Нужно передать список id в поле "items".'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            OrderItem.objects.filter(
                order=basket,
                product_info_id__in=items_ids,
            ).delete()

            basket.refresh_from_db()
            serializer = OrderSerializer(basket)
            return Response(serializer.data, status=status.HTTP_200_OK)

    # ---------- ПОДТВЕРЖДЕНИЕ ЗАКАЗА ----------

    @action(detail=False, methods=['post'], url_path='confirm')
    def confirm(self, request, *args, **kwargs):
        """
        Подтверждение корзины и создание заказа.

        POST /api/v1/orders/confirm/

        Ожидаемый JSON:
        {
          "contact_id": 1
        }
        """
        user = request.user

        # Ищем корзину с товарами
        try:
            basket = Order.objects.get(user=user, state='basket')
        except Order.DoesNotExist:
            return Response(
                {'error': 'Корзина пуста.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not basket.ordered_items.exists():
            return Response(
                {'error': 'Нельзя оформить заказ с пустой корзиной.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contact_id = request.data.get('contact_id')
        if not contact_id:
            return Response(
                {'error': 'Нужно указать "contact_id".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contact = Contact.objects.get(id=contact_id, user=user)
        except Contact.DoesNotExist:
            return Response(
                {'error': 'Контакт не найден или не принадлежит пользователю.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Обновляем заказ: ставим контакт и статус
        basket.contact = contact
        basket.state = 'new'  # или 'confirmed' — как у тебя в ТЗ
        basket.save()

        # Пробуем отправить e-mail (если настроен EMAIL_BACKEND)
        self._send_order_emails(user, basket)

        serializer = OrderSerializer(basket)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _send_order_emails(self, user, order):
        """
        Вспомогательный метод: отправка email клиенту и менеджеру.
        Работает только если настроены EMAIL_* в settings.
        """
        # Письмо клиенту
        if getattr(settings, 'EMAIL_HOST', None) and user.email:
            try:
                send_mail(
                    subject=f'Ваш заказ #{order.id} принят',
                    message=f'Спасибо за заказ #{order.id} на нашем сервисе.',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

        # Письмо менеджеру (если указано)
        manager_email = getattr(settings, 'SHOP_MANAGER_EMAIL', None)
        if getattr(settings, 'EMAIL_HOST', None) and manager_email:
            try:
                send_mail(
                    subject=f'Новый заказ #{order.id}',
                    message=f'Поступил новый заказ #{order.id} от пользователя {user.username}.',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[manager_email],
                    fail_silently=True,
                )
            except Exception:
                pass

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RegisterView(generics.CreateAPIView):
    """
    Регистрация нового пользователя.
    Доступна всем (AllowAny).
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class ProductInfoListView(ListAPIView):
    """
    Эндпоинт для списка товарных предложений.

    Поддерживает фильтры через query-параметры:

    - ?shop_id=1
        товары только из указанного магазина

    - ?category_id=3
        товары только указанной категории

    - ?search=iphone
        поиск по названию товара (product.name, регистронезависимо)

    - ?price_min=50000
      ?price_max=120000
        фильтр по цене "от" и "до"

    - ?in_stock=1
        только товары, у которых quantity > 0

    - ?parameter=Диагональ (дюйм)&value=6.5
        фильтр по параметру товара (через ProductParameter)

    Все фильтры можно комбинировать, например:
    /api/v1/products-info/?shop_id=1&category_id=2&in_stock=1&price_max=120000
    """
    serializer_class = ProductInfoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Базовый queryset:
        - подгружаем связанные product, shop, category через select_related
        - подгружаем параметры товара через prefetch_related('parameters')
        """
        qs = ProductInfo.objects.select_related(
            'product',
            'shop',
            'product__category',
        ).prefetch_related(
            'parameters',
        )

        params = self.request.query_params

        # --- фильтр по магазину ---
        shop_id = params.get('shop_id')
        if shop_id:
            qs = qs.filter(shop_id=shop_id)

        # --- фильтр по категории ---
        category_id = params.get('category_id')
        if category_id:
            qs = qs.filter(product__category_id=category_id)

        # --- поиск по названию товара ---
        search = params.get('search')
        if search:
            qs = qs.filter(product__name__icontains=search)

        # --- фильтр по цене ---
        price_min = params.get('price_min')
        if price_min:
            qs = qs.filter(price__gte=price_min)

        price_max = params.get('price_max')
        if price_max:
            qs = qs.filter(price__lte=price_max)

        # --- только товары в наличии ---
        in_stock = params.get('in_stock')
        if in_stock in ('1', 'true', 'True', 'yes', 'on'):
            qs = qs.filter(quantity__gt=0)

        # --- фильтр по параметру товара ---
        param_name = params.get('parameter')
        param_value = params.get('value')
        if param_name and param_value:
            qs = qs.filter(
                parameters__parameter__name=param_name,
                parameters__value=param_value,
            ).distinct()

        return qs
