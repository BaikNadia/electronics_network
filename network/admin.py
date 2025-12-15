from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from .models import NetworkNode, Product, Employee


class NetworkNodeForm(forms.ModelForm):
    """Кастомная форма с дополнительной валидацией"""

    class Meta:
        model = NetworkNode
        fields = '__all__'

    def clean_debt(self):
        """Валидация поля debt в админке"""
        debt = self.cleaned_data['debt']
        if debt < 0:
            raise forms.ValidationError("Задолженность не может быть отрицательной!")
        if debt > 9999999999999.99:
            raise forms.ValidationError("Задолженность слишком велика!")
        return debt

    def clean_supplier(self):
        """Валидация поставщика для предотвращения циклических зависимостей"""
        supplier = self.cleaned_data['supplier']
        if supplier and self.instance and supplier.id == self.instance.id:
            raise forms.ValidationError("Объект не может быть своим собственным поставщиком!")
        return supplier


class CityFilter(admin.SimpleListFilter):
    """Фильтр по названию города"""
    title = 'Город'
    parameter_name = 'city'

    def lookups(self, request, model_admin):
        cities = NetworkNode.objects.values_list('city', flat=True).distinct()
        return [(city, city) for city in sorted(cities) if city]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(city=self.value())
        return queryset


class SupplierFilter(admin.SimpleListFilter):
    """Фильтр по поставщику"""
    title = 'Поставщик'
    parameter_name = 'supplier'

    def lookups(self, request, model_admin):
        suppliers = NetworkNode.objects.filter(
            node_type__in=[NetworkNode.NodeType.FACTORY, NetworkNode.NodeType.RETAIL]
        ).distinct()
        return [(s.id, s.name) for s in suppliers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(supplier_id=self.value())
        return queryset


@admin.register(NetworkNode)
class NetworkNodeAdmin(admin.ModelAdmin):
    form = NetworkNodeForm  # Используем кастомную форму
    list_display = (
        'name',
        'get_node_type_display',
        'city',
        'country',
        'supplier_link',
        'debt_display',
        'created_at',
        'is_active'
    )
    list_filter = (CityFilter, SupplierFilter, 'country', 'node_type', 'is_active')
    search_fields = ('name', 'email', 'city', 'country', 'street')
    list_editable = ('is_active',)
    actions = ['clear_debt']
    filter_horizontal = ('products',)
    readonly_fields = ('node_type', 'created_at')
    list_per_page = 20

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'node_type', 'supplier', 'is_active', 'created_at')
        }),
        ('Контакты', {
            'fields': ('email', 'country', 'city', 'street', 'house_number')
        }),
        ('Финансы', {
            'fields': ('debt',)
        }),
        ('Продукты', {
            'fields': ('products',)
        }),
    )

    def debt_display(self, obj):
        return f"{obj.debt} ₽"

    debt_display.short_description = 'Задолженность'
    debt_display.admin_order_field = 'debt'

    def supplier_link(self, obj):
        if obj.supplier:
            url = reverse('admin:network_networknode_change', args=[obj.supplier.id])
            return format_html('<a href="{}">{}</a>', url, obj.supplier.name)
        return "-"

    supplier_link.short_description = 'Поставщик'
    supplier_link.admin_order_field = 'supplier'

    def clear_debt(self, request, queryset):
        updated = queryset.update(debt=0)
        self.message_user(request, f'Задолженность очищена у {updated} объектов')

    clear_debt.short_description = 'Очистить задолженность перед поставщиком'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'release_date')
    list_filter = ('release_date',)
    search_fields = ('name', 'model')
    date_hierarchy = 'release_date'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)

    def username(self, obj):
        return obj.user.username

    username.short_description = 'Имя пользователя'
    username.admin_order_field = 'user__username'

    def email(self, obj):
        return obj.user.email

    email.short_description = 'Email'
    email.admin_order_field = 'user__email'
