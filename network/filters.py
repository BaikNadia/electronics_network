from django_filters import rest_framework as filters
from .models import NetworkNode


class NetworkNodeFilter(filters.FilterSet):
    country = filters.CharFilter(field_name='country', lookup_expr='iexact')
    city = filters.CharFilter(field_name='city', lookup_expr='iexact')
    min_debt = filters.NumberFilter(field_name='debt', lookup_expr='gte')
    max_debt = filters.NumberFilter(field_name='debt', lookup_expr='lte')

    class Meta:
        model = NetworkNode
        fields = ['country', 'city', 'node_type', 'is_active']
