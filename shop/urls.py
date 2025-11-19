from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ShopViewSet,
    CategoryViewSet,
    ProductViewSet,
    OrderViewSet,
    ContactViewSet,      # ← ЭТО НУЖНО ДОБАВИТЬ!
)

router = DefaultRouter()
router.register(r'shops', ShopViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'contacts', ContactViewSet, basename='contacts')

urlpatterns = [
    path('', include(router.urls)),
]