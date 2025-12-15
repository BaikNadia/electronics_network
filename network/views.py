from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import NetworkNode, Product, Employee
from .serializers import (
    NetworkNodeSerializer,
    NetworkNodeCreateSerializer,
    NetworkNodeUpdateSerializer,
    ProductSerializer,
    EmployeeSerializer
)
from .permissions import IsActiveEmployee
from .filters import NetworkNodeFilter


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с звеньями сети.
    Запрещено обновление поля 'debt' через API.
    """
    queryset = NetworkNode.objects.all()
    permission_classes = [IsActiveEmployee]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NetworkNodeFilter
    search_fields = ['name', 'email', 'city', 'country']
    ordering_fields = ['created_at', 'name', 'debt']

    def get_serializer_class(self):
        if self.action == 'create':
            return NetworkNodeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NetworkNodeUpdateSerializer
        return NetworkNodeSerializer

    def create(self, request, *args, **kwargs):
        # Устанавливаем debt в 0 по умолчанию, если не указано
        if 'debt' not in request.data:
            request.data['debt'] = 0
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Запрещаем обновление debt через API
        if 'debt' in request.data:
            return Response(
                {'error': 'Обновление задолженности через API запрещено'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def filter_by_country(self, request):
        """Кастомный endpoint для фильтрации по стране"""
        country = request.query_params.get('country', None)
        if country:
            queryset = self.get_queryset().filter(country__iexact=country)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(
            {'error': 'Параметр country обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def high_debt(self, request):
        """Endpoint для получения объектов с задолженностью > 0"""
        queryset = self.get_queryset().filter(debt__gt=0)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с продуктами.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsActiveEmployee]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'model']
    ordering_fields = ['release_date', 'name']


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления сотрудниками.
    Только для администраторов.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'user__email']
