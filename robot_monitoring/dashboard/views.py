
from django.shortcuts import render, redirect
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Robot, Alert, RobotGroup  # Убедитесь, что эти модели существуют

from .utils import get_dashboard_data


def dashboard_view(request):
    """Представление для главного дашборда без аутентификации"""

    # Основные данные по роботам
    robots = Robot.objects.all()
    total_robots = robots.count()
    active_robots = robots.filter(status__in=['active', 'idle']).count()
    maintenance_robots = robots.filter(status='maintenance').count()

    # Данные по оповещениям (обновлено)
    critical_alerts = Alert.objects.filter(alert_type='critical', resolved=False)
    warning_alerts = Alert.objects.filter(alert_type='warning', resolved=False)
    maintenance_alerts = Alert.objects.filter(alert_type='maintenance', resolved=False)

    # Счетчики для верхних блоков
    critical_alerts_count = critical_alerts.count()
    warning_alerts_count = warning_alerts.count()
    maintenance_alerts_count = maintenance_alerts.count()

    # Группы роботов
    robot_groups = RobotGroup.objects.all().prefetch_related('robots')

    # Последние активные роботы
    recent_robots = robots.order_by('-updated_at')[:5]

    # Статистика по местоположениям
    location_stats = robots.values('location').annotate(
        count=Count('id'),
        avg_battery=Avg('battery_level'),
        avg_temperature=Avg('temperature')
    )

    context = {
        'total_robots': total_robots,
        'active_robots': active_robots,
        'maintenance_robots': maintenance_robots,
        'critical_alerts': critical_alerts_count,  # Обновлено
        'warning_alerts': warning_alerts_count,  # Обновлено
        'maintenance_alerts': maintenance_alerts_count,  # Обновлено
        'critical_alerts_list': critical_alerts,  # Добавлено
        'warning_alerts_list': warning_alerts,  # Добавлено
        'maintenance_alerts_list': maintenance_alerts,  # Добавлено
        'robot_groups': robot_groups,
        'recent_robots': recent_robots,
        'location_stats': location_stats,
        'stats': {
            'total_robots': total_robots,
            'active_robots': active_robots,
            'maintenance_robots': maintenance_robots,
            'critical_alerts': critical_alerts_count,
            'warning_alerts': warning_alerts_count,
            'maintenance_alerts': maintenance_alerts_count,
        },
        'current_page': 'dashboard'
    }

    return render(request, 'dashboard/dashboard.html', context)


def create_test_robots(request):
    """Создает тестовых роботов для демонстрации"""
    try:
        # Получаем первого пользователя (админа)
        user = User.objects.first()

        # Если нет пользователей, создаем суперпользователя
        if not user:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            messages.success(request, 'Создан суперпользователь: admin / admin123')

        # Данные для тестовых роботов
        test_robots = [
            {
                "robot_id": "RBT-001",
                "name": "Складской робот #1",
                "robot_type": "warehouse",
                "status": "active",
                "battery_level": 85.3,
                "temperature": 32.1,
                "location": "Склад А, зона 1",
                "current_task": "Транспортировка грузов"
            },
            {
                "robot_id": "RBT-002",
                "name": "Производственный робот #2",
                "robot_type": "production",
                "status": "critical",
                "battery_level": 15.2,
                "temperature": 52.3,
                "location": "Цех 2, станок 5",
                "current_task": "Обработка деталей"
            },
            {
                "robot_id": "RBT-003",
                "name": "Робот-инспектор #3",
                "robot_type": "inspection",
                "status": "warning",
                "battery_level": 42.7,
                "temperature": 38.6,
                "location": "Склад Б, зона контроля",
                "current_task": "Патрулирование"
            },
            {
                "robot_id": "RBT-004",
                "name": "Робот-доставщик #4",
                "robot_type": "delivery",
                "status": "maintenance",
                "battery_level": 78.9,
                "temperature": 31.4,
                "location": "Зона погрузки",
                "current_task": "Плановое обслуживание"
            },
            {
                "robot_id": "RBT-005",
                "name": "Уборочный робот #5",
                "robot_type": "cleaning",
                "status": "warning",
                "battery_level": 28.5,
                "temperature": 41.2,
                "location": "Административный корпус",
                "current_task": "Уборка помещений"
            }
        ]

        # Создаем роботов
        created_count = 0
        for robot_data in test_robots:
            robot, created = Robot.objects.get_or_create(
                robot_id=robot_data["robot_id"],
                defaults={
                    **robot_data,
                    "owner": user
                }
            )
            if created:
                created_count += 1

        messages.success(request, f'Успешно создано {created_count} тестовых роботов!')

    except Exception as e:
        messages.error(request, f'Ошибка при создании роботов: {str(e)}')
        print(f"Ошибка при создании роботов: {str(e)}")

    # Перенаправляем на дашборд
    return redirect('dashboard')

def custom_404(request, exception):
    return render(request, '404.html', status=404)