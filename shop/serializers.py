from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    Shop, Category, Product, ProductInfo, Order, OrderItem,
    Parameter, ProductParameter, Contact
)
from .tasks import generate_product_thumbnails


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter_name = serializers.CharField(source='parameter.name', read_only=True)

    class Meta:
        model = ProductParameter
        fields = ['id', 'parameter', 'parameter_name', 'value']


class ProductInfoSerializer(serializers.ModelSerializer):
    parameters = ProductParameterSerializer(many=True, read_only=True)

    product = serializers.CharField(source='product.name', read_only=True)
    shop = serializers.CharField(source='shop.name', read_only=True)
    category = serializers.CharField(source='product.category.name', read_only=True)

    class Meta:
        model = ProductInfo
        fields = [
            'id', 'model', 'price', 'price_rrc', 'quantity',
            'product', 'shop', 'category', 'parameters',
        ]


# ✅ для чтения (в ответах API)
class ProductReadSerializer(serializers.ModelSerializer):
    product_infos = ProductInfoSerializer(many=True, read_only=True)
    image_small = serializers.SerializerMethodField()
    image_medium = serializers.SerializerMethodField()
    image_large = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category',
            'image', 'image_small', 'image_medium', 'image_large',
            'product_infos'
        ]

    def get_image_small(self, obj):
        return obj.image_small.url if obj.image else None

    def get_image_medium(self, obj):
        return obj.image_medium.url if obj.image else None

    def get_image_large(self, obj):
        return obj.image_large.url if obj.image else None

# ✅ для записи (upload/update), тут запускаем Celery
class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

    def update(self, instance, validated_data):
        image_before = instance.image
        instance = super().update(instance, validated_data)

        image_after = instance.image
        if image_after and image_after != image_before:
            generate_product_thumbnails.delay(instance.id)

        return instance


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product_info.product.name', read_only=True)
    shop = serializers.CharField(source='product_info.shop.name', read_only=True)
    price = serializers.DecimalField(
        source='product_info.price', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'product', 'shop', 'price', 'quantity', 'order']
        extra_kwargs = {'order': {'read_only': True}}


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemSerializer(source='items', many=True, read_only=True)
    total_sum = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'status', 'contact',
            'ordered_items', 'total_sum',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'created_at', 'updated_at']

    def get_total_sum(self, obj):
        total = 0
        for item in obj.items.select_related('product_info'):
            total += item.product_info.price * item.quantity
        return total


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'user', 'city', 'address', 'phone']
        read_only_fields = ['user']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )

