from django.contrib import admin
from django.urls import path, include
from baton.autodiscover import admin
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from shop.views import RegisterView, ProductInfoListView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('baton/', include('baton.urls')),
    # Регистрация
    path('api/v1/auth/register/', RegisterView.as_view(), name='register'),

    # JWT логин и обновление токена
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Эндпоинт со списком товарных предложений
    path('api/v1/products-info/', ProductInfoListView.as_view(), name='products-info'),

    # Все остальные эндпоинты из приложения shop (магазины, категории, товары, заказы, контакты)
    path('api/v1/', include('shop.urls')),

    # Логин/логаут для DRF Browsable API
    path('api-auth/', include('rest_framework.urls')),

    # ----- DRF Spectacular -----

    # OpenAPI schema (JSON/YAML)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path(
        'api/schema/swagger/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),

    # ReDoc
    path(
        'api/schema/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
    path('oauth/', include('social_django.urls', namespace='social')),
]


