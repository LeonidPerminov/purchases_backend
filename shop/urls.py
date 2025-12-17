from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ShopViewSet,
    CategoryViewSet,
    ProductViewSet,
    OrderViewSet,
    ContactViewSet,
)

from .views import SentryDebugAPIView
from .views_bench import CacheBenchmarkView

router = DefaultRouter()
router.register(r'shops', ShopViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'contacts', ContactViewSet, basename='contacts')

urlpatterns = [
    path('', include(router.urls)),
    path("debug/sentry/", SentryDebugAPIView.as_view(), name="debug-sentry"),
    path("bench/cache/", CacheBenchmarkView.as_view(), name="bench-cache"),
]