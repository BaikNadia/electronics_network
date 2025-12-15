from rest_framework import permissions
from .models import Employee


class IsActiveEmployee(permissions.BasePermission):
    """
    Разрешение только для активных сотрудников
    """

    def has_permission(self, request, view):
        # Проверяем аутентификацию
        if not request.user or not request.user.is_authenticated:
            return False

        # Проверяем, является ли пользователь активным сотрудником
        try:
            employee = Employee.objects.get(user=request.user)
            return employee.is_active
        except Employee.DoesNotExist:
            # Если запись Employee не существует, создаем её
            employee, created = Employee.objects.get_or_create(
                user=request.user,
                defaults={'is_active': True}
            )
            return employee.is_active
