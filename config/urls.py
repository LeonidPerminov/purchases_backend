from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from shop.views import RegisterView, ProductInfoListView  # ← добавили ProductInfoListView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Регистрация
    path('api/v1/auth/register/', RegisterView.as_view(), name='register'),

    # JWT логин и обновление токена
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Эндпоинт со списком товарных предложений
    path('api/v1/products-info/', ProductInfoListView.as_view(), name='products-info'),

    # Все остальные эндпоинты из приложения shop (магазины, категории, товары, заказы, контакты)
    path('api/v1/', include('shop.urls')),  # ← ОСТАВЛЯЕМ ТОЛЬКО ОДНУ СТРОКУ

    # Логин/логаут для DRF Browsable API
    path('api-auth/', include('rest_framework.urls')),
]

