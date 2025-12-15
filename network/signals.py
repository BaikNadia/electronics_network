from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Employee


@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    """Автоматическое создание профиля сотрудника при создании пользователя"""
    if created:
        Employee.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_employee_profile(sender, instance, **kwargs):
    """Сохранение профиля сотрудника при сохранении пользователя"""
    try:
        instance.employee_profile.save()
    except Employee.DoesNotExist:
        Employee.objects.create(user=instance)
