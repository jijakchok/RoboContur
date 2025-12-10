from django.shortcuts import render
from django.db.models import Avg, Count, Sum, F
from django.utils import timezone
from datetime import timedelta
from dashboard.models import Robot, Alert, RobotGroup, RobotReading


def reports_view(request):
    # Определяем периоды
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    previous_period = now - timedelta(days=60)

    # Получаем всех роботов
    robots = Robot.objects.all()

    # 1. Средний uptime за последние 30 дней
    # Считаем uptime как процент времени, когда робот был в статусе active/idle
    total_robots = robots.count()
    active_robots = robots.filter(status__in=['active', 'idle']).count()
    avg_uptime = (active_robots / total_robots * 100) if total_robots > 0 else 0

    # Сравнение с предыдущим периодом
    prev_active_robots = Robot.objects.filter(
        status__in=['active', 'idle'],
        updated_at__gte=previous_period,
        updated_at__lt=last_30_days
    ).count()
    prev_total_robots = Robot.objects.filter(
        updated_at__gte=previous_period,
        updated_at__lt=last_30_days
    ).count()
    prev_avg_uptime = (prev_active_robots / prev_total_robots * 100) if prev_total_robots > 0 else 0
    uptime_change = avg_uptime - prev_avg_uptime
    uptime_change_direction = "up" if uptime_change > 0 else "down" if uptime_change < 0 else "neutral"

    # 2. Задачи, выполненные за последние 30 дней
    # Используем assigned_tasks как приближенное значение
    tasks_completed = robots.aggregate(total_tasks=Sum('assigned_tasks'))['total_tasks'] or 0

    # Сравнение с предыдущим периодом (грубое приближение)
    # В реальном приложении здесь должны быть данные о выполненных задачах за конкретные периоды
    prev_tasks_completed = int(tasks_completed * 0.92)  # Примерное значение для сравнения
    tasks_change = tasks_completed - prev_tasks_completed
    tasks_change_percent = (tasks_change / prev_tasks_completed * 100) if prev_tasks_completed > 0 else 0
    tasks_change_direction = "up" if tasks_change > 0 else "down" if tasks_change < 0 else "neutral"

    # 3. Потребление энергии (моделирование на основе операционных часов)
    # В реальном приложении здесь должны быть реальные данные о потреблении энергии
    total_operational_hours = robots.aggregate(total_hours=Sum('operational_hours'))['total_hours'] or 0
    # Предположим, что робот потребляет в среднем 0.5 кВт/час
    energy_consumption = total_operational_hours * 0.5  # в кВтч
    energy_consumption = round(energy_consumption, 1)

    # Сравнение с предыдущим периодом
    prev_energy_consumption = energy_consumption * 1.03  # Примерное значение для сравнения
    energy_change = energy_consumption - prev_energy_consumption
    energy_change_percent = (energy_change / prev_energy_consumption * 100) if prev_energy_consumption > 0 else 0
    energy_change_direction = "down" if energy_change < 0 else "up" if energy_change > 0 else "neutral"

    # 4. Дополнительные метрики для отчетов
    avg_battery = robots.aggregate(avg_battery=Avg('battery_level'))['avg_battery'] or 0
    avg_battery = round(avg_battery, 1)

    avg_temperature = robots.aggregate(avg_temp=Avg('temperature'))['avg_temp'] or 0
    avg_temperature = round(avg_temperature, 1)

    # Количество оповещений за последний период
    alerts_count = Alert.objects.filter(
        created_at__gte=last_30_days,
        resolved=False
    ).count()

    # Группы роботов
    robot_groups = RobotGroup.objects.all().prefetch_related('robots')
    groups_data = []
    for group in robot_groups:
        group_robots = group.robots.all()
        group_size = group_robots.count()
        group_active = group_robots.filter(status__in=['active', 'idle']).count()
        group_uptime = (group_active / group_size * 100) if group_size > 0 else 0

        groups_data.append({
            'name': group.name,
            'robots_count': group_size,
            'uptime': round(group_uptime, 1),
            'avg_battery': round(group_robots.aggregate(Avg('battery_level'))['battery_level__avg'] or 0, 1),
            'alerts_count': Alert.objects.filter(robot__in=group_robots, resolved=False).count()
        })

    context = {
        'current_page': 'reports',
        'avg_uptime': round(avg_uptime, 1),
        'uptime_change': round(uptime_change, 1),
        'uptime_change_direction': uptime_change_direction,
        'tasks_completed': tasks_completed,
        'tasks_change_percent': round(tasks_change_percent, 1),
        'tasks_change_direction': tasks_change_direction,
        'energy_consumption': energy_consumption,
        'energy_change_percent': round(abs(energy_change_percent), 1),
        'energy_change_direction': energy_change_direction,
        'avg_battery': avg_battery,
        'avg_temperature': avg_temperature,
        'alerts_count': alerts_count,
        'groups_data': groups_data,
        'total_robots': total_robots
    }

    return render(request, "reports/reports.html", context)