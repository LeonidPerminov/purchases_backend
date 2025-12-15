from django.conf import settings
from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill



class Shop(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    url = models.URLField(blank=True, null=True, verbose_name="Сайт")
    is_active = models.BooleanField(default=True, verbose_name="Принимает заказы")

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    shops = models.ManyToManyField(
        Shop,
        related_name="categories",
        blank=True,
        verbose_name="Магазины",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE,
        verbose_name="Категория",
    )

    image = models.ImageField(
        upload_to='products/originals/',
        blank=True,
        null=True,
        verbose_name="Изображение"
    )

    image_small = ImageSpecField(
        source='image',
        processors=[ResizeToFill(100, 100)],
        format='JPEG',
        options={'quality': 80}
    )

    image_medium = ImageSpecField(
        source='image',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 85}
    )

    image_large = ImageSpecField(
        source='image',
        processors=[ResizeToFill(800, 800)],
        format='JPEG',
        options={'quality': 90}
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self) -> str:
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="infos",
        on_delete=models.CASCADE,
        verbose_name="Товар",
    )
    shop = models.ForeignKey(
        Shop,
        related_name="product_infos",
        on_delete=models.CASCADE,
        verbose_name="Магазин",
    )
    external_id = models.PositiveIntegerField(verbose_name="ID в системе магазина")
    model = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Модель / артикул",
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name="Остаток")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
    )
    price_rrc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="РРЦ",
    )

    class Meta:
        verbose_name = "Информация о товаре"
        verbose_name_plural = "Информация о товарах"
        unique_together = ("shop", "external_id")

    def __str__(self) -> str:
        return f"{self.product} ({self.shop})"


class Parameter(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Параметры"

    def __str__(self) -> str:
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(
        ProductInfo,
        related_name="parameters",
        on_delete=models.CASCADE,
        verbose_name="Товар",
    )
    parameter = models.ForeignKey(
        Parameter,
        related_name="product_parameters",
        on_delete=models.CASCADE,
        verbose_name="Параметр",
    )
    value = models.CharField(max_length=255, verbose_name="Значение")

    class Meta:
        verbose_name = "Параметр товара"
        verbose_name_plural = "Параметры товара"
        unique_together = ("product_info", "parameter")

    def __str__(self) -> str:
        return f"{self.parameter}: {self.value}"


class Contact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="contacts",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    city = models.CharField(max_length=100, verbose_name="Город")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    phone = models.CharField(max_length=32, verbose_name="Телефон")

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"

    def __str__(self) -> str:
        return f"{self.city}, {self.address}"


class Order(models.Model):
    STATUS_BASKET = "basket"
    STATUS_NEW = "new"
    STATUS_CONFIRMED = "confirmed"
    STATUS_SENT = "sent"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_BASKET, "Корзина"),
        (STATUS_NEW, "Новый"),
        (STATUS_CONFIRMED, "Подтверждён"),
        (STATUS_SENT, "Отправлен"),
        (STATUS_DELIVERED, "Доставлен"),
        (STATUS_CANCELLED, "Отменён"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_BASKET,
        verbose_name="Статус",
    )
    contact = models.ForeignKey(
        Contact,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Контакт",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Заказ #{self.pk} ({self.get_status_display()})"

    @property
    def total_sum(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="ordered_items",
        on_delete=models.CASCADE,
        verbose_name="Заказ",
    )
    product_info = models.ForeignKey(
        ProductInfo,
        related_name="order_items",
        on_delete=models.CASCADE,
        verbose_name="Товар",
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
        unique_together = ("order", "product_info")

    def __str__(self) -> str:
        return f"{self.product_info} x {self.quantity}"

    @property
    def total_price(self):
        return self.quantity * self.product_info.price