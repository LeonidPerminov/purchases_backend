import os
import django
import yaml

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from shop.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter

# ✅ исправили путь
file_path = os.path.join(os.path.dirname(__file__), "data", "shop1.yaml")

with open(file_path, "r", encoding="utf-8") as file:
    data = yaml.safe_load(file)

# 1️⃣ Магазин
shop_name = data["shop"]
shop, _ = Shop.objects.get_or_create(name=shop_name)

# 2️⃣ Категории
categories_map = {}

for category_data in data["categories"]:
    cat_id = category_data["id"]
    cat_name = category_data["name"]

    category, _ = Category.objects.get_or_create(name=cat_name)
    category.shops.add(shop)

    categories_map[cat_id] = category

# 3️⃣ Товары
for product_data in data["goods"]:
    category_id = product_data["category"]
    category = categories_map.get(category_id)
    if category is None:
        continue

    product, _ = Product.objects.get_or_create(
        name=product_data["name"],
        category=category,
    )

    # ✅ используем update_or_create
    product_info, _ = ProductInfo.objects.update_or_create(
        product=product,
        shop=shop,
        external_id=product_data["id"],
        defaults={
            "model": product_data.get("model", ""),
            "price": product_data["price"],
            "price_rrc": product_data.get("price_rrc") or product_data["price"],
            "quantity": product_data.get("quantity", 0),
        },
    )

    for param_name, param_value in product_data.get("parameters", {}).items():
        parameter, _ = Parameter.objects.get_or_create(name=param_name)
        ProductParameter.objects.update_or_create(
            product_info=product_info,
            parameter=parameter,
            defaults={"value": str(param_value)},
        )

print("✅ Данные успешно загружены в базу!")
