from rest_framework import serializers
from .models import Shop, Category, Product, ProductInfo, Order, OrderItem, Parameter, ProductParameter, Contact
from django.contrib.auth.models import User

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductParameterSerializer(serializers.ModelSerializer):
    parameter_name = serializers.CharField(
        source='parameter.name',
        read_only=True
    )

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
            'id',
            'model',
            'price',
            'price_rrc',
            'quantity',
            'product',
            'shop',
            'category',
            'parameters',
        ]

class ProductSerializer(serializers.ModelSerializer):
    product_infos = ProductInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'product_infos']

class OrderItemSerializer(serializers.ModelSerializer):
    # Дополнительные поля только для чтения, чтобы красиво показывать корзину
    product = serializers.CharField(
        source='product_info.product.name',
        read_only=True
    )
    shop = serializers.CharField(
        source='product_info.shop.name',
        read_only=True
    )
    price = serializers.DecimalField(
        source='product_info.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = OrderItem
        # product_info и quantity — на запись,
        # остальные — для удобного отображения
        fields = [
            'id',
            'product_info',
            'product',
            'shop',
            'price',
            'quantity',
            'order',
        ]
        extra_kwargs = {
            'order': {'read_only': True},       # ордер проставим во viewset-е
            'product_info': {'write_only': False},
        }


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemSerializer(many=True, read_only=True)
    total_sum = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'state', 'dt', 'ordered_items', 'total_sum']
        read_only_fields = ['user', 'state', 'dt', 'total_sum']

    def get_total_sum(self, obj):
        # суммируем цену * количество для всех позиций
        total = 0
        for item in obj.ordered_items.select_related('product_info'):
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
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        return user

