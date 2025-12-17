Purchases Backend
![coverage](https://img.shields.io/badge/coverage-78%25-brightgreen)

Дипломный проект (Netology).
API на Django REST Framework для управления покупками и корзиной.

Проект включает:

магазины

категории

товары

товарные предложения (ProductInfo)

параметры товаров

корзину

оформление заказа

регистрацию пользователей

загрузку данных из YAML

Как запустить проект
1. Клонировать репозиторий
git clone https://github.com/LeonidPerminov/purchases_backend.git
cd purchases_backend

2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

3. Установить зависимости
pip install -r requirements.txt

4. Выполнить миграции
python manage.py migrate

5. Создать суперпользователя (по желанию)
python manage.py createsuperuser

6. Запустить сервер
python manage.py runserver


API будет доступен по адресу:
http://127.0.0.1:8000/api/v1/

Загрузка данных из YAML

В проекте есть скрипт:

load_yaml_data.py


И файл с данными:

data/shop1.yaml


Чтобы загрузить товары в базу:

python load_yaml_data.py


После этого в базе появятся магазин, категории, товары, предложения и параметры.

Аутентификация

Проект использует JWT (через simplejwt).

Регистрация

POST /api/v1/auth/register/

Пример JSON:

{
  "username": "test",
  "email": "test@example.com",
  "password": "123456"
}

Получение токена

POST /api/v1/auth/token/

Обновление токена

POST /api/v1/auth/token/refresh/

Основные эндпоинты
Общая справочная информация
Магазины

GET /api/v1/shops/

Категории

GET /api/v1/categories/

Товары

GET /api/v1/products/

Товарные предложения (ProductInfo)

GET /api/v1/products-info/

Фильтрация ProductInfo

Эндпоинт поддерживает фильтры через параметры URL:

По магазину

?shop_id=1

По категории

?category_id=3

По поиску названия товара

?search=iphone

По цене

?price_min=50000
?price_max=120000

Только товары в наличии

?in_stock=1

По параметру товара

?parameter=Диагональ (дюйм)&value=6.5

Можно комбинировать:
/api/v1/products-info/?shop_id=1&category_id=2&in_stock=1

Корзина и заказы
Получить корзину

GET /api/v1/orders/basket/

Добавить товары в корзину

POST /api/v1/orders/basket/

Пример:

{
  "items": [
    {"product_info": 1, "quantity": 2},
    {"product_info": 3, "quantity": 1}
  ]
}

Удалить товары из корзины

DELETE /api/v1/orders/basket/

{
  "items": [1, 3]
}

Подтвердить заказ

POST /api/v1/orders/confirm/

{
  "contact_id": 1
}

Контакты пользователя
Список

GET /api/v1/contacts/

Создание

POST /api/v1/contacts/

Стек технологий

Python 3.10

Django 5

Django REST Framework

SimpleJWT

SQLite

YAML (PyYAML)

Asynchronous thumbnails generation

Product images are stored in Product.image

Thumbnails (100x100, 300x300, 800x800) are generated via django-imagekit

Thumbnail generation is triggered asynchronously via Celery task shop.tasks.generate_product_thumbnails

Celery worker (Windows):
python -m celery -A config.celery worker -l info -P solo

Для включения error tracking укажите SENTRY_DSN в .env.
Если переменная не задана — Sentry отключён.

## ORM query caching (Redis + django-cacheops)

В проекте включено кэширование ORM-запросов чтения через Redis с помощью `django-cacheops`.
Кэш включается флагом `CACHEOPS_ENABLED=1`.

### Env
- `REDIS_URL` — адрес Redis
- `CACHEOPS_REDIS_DB` — номер Redis DB для кэша (по умолчанию 2)
- `CACHEOPS_ENABLED` — 1/0

### Benchmark endpoint
`GET /api/bench/cache/`

Первый запрос прогревает кэш, повторные запросы должны быть быстрее.

### Results (local)
- Before cacheops: 1st = X ms, 2nd = Y ms, 3rd = Z ms
- After cacheops:  1st = X ms, 2nd = Y ms, 3rd = Z ms

Автор

Леонид Перминов
Дипломный проект на курсе «Python-разработчик» (Netology)