from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.apps import apps
from .models import Order


@shared_task
def send_order_emails(order_id: int, user_id: int) -> None:
    """
    Асинхронная задача:
    отправить письма клиенту и менеджеру после оформления заказа.
    Выполняется воркером Celery, а не в HTTP-запросе.
    """
    # --- аккуратно достаём Order и User ---
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    # --- письмо клиенту ---
    if getattr(settings, "EMAIL_HOST", None) and user.email:
        try:
            send_mail(
                subject=f"Ваш заказ #{order.id} принят",
                message=f"Спасибо за заказ #{order.id} на нашем сервисе.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            # в задаче лучше не падать из-за почты
            pass

    # --- письмо менеджеру (если настроено) ---
    manager_email = getattr(settings, "SHOP_MANAGER_EMAIL", None)
    if getattr(settings, "EMAIL_HOST", None) and manager_email:
        try:
            send_mail(
                subject=f"Новый заказ #{order.id}",
                message=(
                    f"Поступил новый заказ #{order.id} "
                    f"от пользователя {user.username}."
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[manager_email],
                fail_silently=True,
            )
        except Exception:
            pass

@shared_task
def generate_product_thumbnails(product_id: int) -> None:
    """
    Forces generation of Product thumbnails (ImageKit cache) in background.
    """
    Product = apps.get_model("shop", "Product")
    product = Product.objects.filter(id=product_id).first()
    if not product or not product.image:
        return

    # Touching .url triggers ImageKit generation & caching
    _ = product.image_small.url
    _ = product.image_medium.url
    _ = product.image_large.url
