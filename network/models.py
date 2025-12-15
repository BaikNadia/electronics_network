from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse


class NetworkNode(models.Model):
    """Модель звена сети по продаже электроники"""

    objects = None

    class NodeType(models.IntegerChoices):
        FACTORY = 0, 'Завод'
        RETAIL = 1, 'Розничная сеть'
        ENTREPRENEUR = 2, 'Индивидуальный предприниматель'

    name = models.CharField(
        max_length=255,
        verbose_name='Название',
        unique=True
    )

    # Контакты
    email = models.EmailField(verbose_name='Email')
    country = models.CharField(max_length=100, verbose_name='Страна')
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=255, verbose_name='Улица')
    house_number = models.CharField(max_length=20, verbose_name='Номер дома')

    # Иерархия
    supplier = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients',
        verbose_name='Поставщик'
    )

    node_type = models.IntegerField(
        choices=NodeType.choices,
        verbose_name='Тип звена',
        editable=False
    )

    # Продукты
    products = models.ManyToManyField(
        'Product',
        related_name='network_nodes',
        verbose_name='Продукты',
        blank=True
    )

    # Задолженность с улучшенной валидацией
    debt = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[
            MinValueValidator(0, message='Задолженность не может быть отрицательной'),
            MaxValueValidator(9999999999999.99, message='Задолженность слишком велика')
        ],
        default=0,
        verbose_name='Задолженность перед поставщиком'
    )

    # Время создания
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания'
    )

    # Активность
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный'
    )

    class Meta:
        verbose_name = 'Звено сети'
        verbose_name_plural = 'Звенья сети'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.name}"

    def clean(self):
        """Дополнительная валидация при сохранении"""
        super().clean()

        # Проверка, что debt не отрицательный
        if self.debt < 0:
            raise ValidationError({
                'debt': 'Задолженность не может быть отрицательной'
            })

        # Проверка циклических зависимостей
        if self.supplier and self.supplier.id == self.id:
            raise ValidationError({
                'supplier': 'Объект не может быть своим собственным поставщиком'
            })

        # Проверка глубоких цепочек
        if self.supplier and self.supplier.supplier and self.supplier.supplier.id == self.id:
            raise ValidationError({
                'supplier': 'Обнаружена циклическая зависимость в цепочке поставок'
            })

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова валидации"""
        # Автоматическое определение типа на основе поставщика
        if self.supplier is None:
            self.node_type = self.NodeType.FACTORY
        elif self.supplier.node_type == self.NodeType.FACTORY:
            self.node_type = self.NodeType.RETAIL
        else:
            self.node_type = self.NodeType.ENTREPRENEUR

        # Вызов полной валидации перед сохранением
        self.full_clean()

        # Вызов оригинального save
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('admin:network_networknode_change', args=[self.id])


class Product(models.Model):
    """Модель продукта"""
    objects = None
    name = models.CharField(max_length=255, verbose_name='Название')
    model = models.CharField(max_length=255, verbose_name='Модель')
    release_date = models.DateField(verbose_name='Дата выхода на рынок')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['-release_date']

    def __str__(self):
        return f"{self.name} ({self.model})"


class Employee(models.Model):
    """Модель сотрудника для контроля доступа к API"""
    objects = None
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активный сотрудник')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return f"{self.user.username} - {'Активен' if self.is_active else 'Неактивен'}"
