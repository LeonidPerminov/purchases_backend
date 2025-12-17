from time import perf_counter

from django.db import connection
from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Product  # если у тебя модель называется иначе — замени


class CacheBenchmarkView(APIView):
    """
    Benchmark endpoint for ORM caching via Redis (cacheops).
    1st request warms cache, next requests should be faster.
    """

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        start = perf_counter()

        # "Тяжёлый" запрос: сортировка + агрегация (показательный пример)
        qs = (
            Product.objects
            .annotate(cnt=Count("id"))
            .order_by("-cnt", "id")[:200]
        )

        ids = list(qs.values_list("id", flat=True))

        # Второй запрос: выборка данных по id
        items = list(
            Product.objects.filter(id__in=ids).values("id", "name")[:200]
        )

        elapsed_ms = (perf_counter() - start) * 1000
        queries_count = len(connection.queries)

        resp = Response({
            "elapsed_ms": round(elapsed_ms, 2),
            "queries_count": queries_count,
            "items": len(items),
            "cacheops_enabled": True,
        })
        resp["X-Response-Time-ms"] = f"{elapsed_ms:.2f}"
        return resp