from rest_framework import serializers
from decimal import Decimal
from .models import NetworkNode, Product, Employee


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class NetworkNodeSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    node_type_display = serializers.CharField(source='get_node_type_display', read_only=True)

    class Meta:
        model = NetworkNode
        fields = [
            'id',
            'name',
            'email',
            'country',
            'city',
            'street',
            'house_number',
            'supplier',
            'supplier_name',
            'node_type',
            'node_type_display',
            'products',
            'debt',
            'created_at',
            'is_active'
        ]
        read_only_fields = ['debt', 'created_at', 'node_type']


class NetworkNodeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания с автоматическим определением node_type"""
    products = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.all(),
        required=False
    )

    def validate_debt(self, value):
        """Кастомная валидация для поля debt"""
        if value < Decimal('0'):
            raise serializers.ValidationError(
                "Задолженность не может быть отрицательной"
            )

        # Проверка максимального значения
        if value > Decimal('9999999999999.99'):
            raise serializers.ValidationError(
                "Задолженность слишком велика"
            )

        return value

    def validate(self, data):
        """Общая валидация данных"""
        # Проверка циклических зависимостей (если есть ID у существующего объекта)
        if self.instance and 'supplier' in data:
            supplier = data['supplier']
            if supplier and supplier.id == self.instance.id:
                raise serializers.ValidationError({
                    'supplier': 'Объект не может быть своим собственным поставщиком'
                })

        return data

    class Meta:
        model = NetworkNode
        fields = '__all__'
        read_only_fields = ['created_at', 'node_type']
        extra_kwargs = {
            'debt': {'required': False, 'default': 0}
        }


class NetworkNodeUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления с запретом изменения debt"""

    def validate(self, data):
        """Запрещаем обновление поля debt через API"""
        if 'debt' in data:
            raise serializers.ValidationError({
                'debt': 'Обновление задолженности через API запрещено'
            })
        return data

    class Meta:
        model = NetworkNode
        fields = [
            'name',
            'email',
            'country',
            'city',
            'street',
            'house_number',
            'supplier',
            'products',
            'is_active'
        ]


class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'username', 'email', 'is_active', 'created_at']
