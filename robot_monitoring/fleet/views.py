from django.shortcuts import render
from dashboard.models import Robot, RobotGroup, RobotReading
from django.db.models import Count, Avg, Q, FloatField, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta


def fleet_view(request):
    # Получаем все роботы
    robots = Robot.objects.all()

    # Общие метрики
    total_fleet_size = robots.count()

    # 1. Среднее время работы в процентах (uptime) для всего флота
    now = timezone.now()
    period_start = now - timedelta(days=7)  # Анализ за последнюю неделю

    # Получаем все показания за период
    all_readings = RobotReading.objects.filter(
        timestamp__gte=period_start
    ).values('robot_id').annotate(
        total_readings=Count('id'),
        active_readings=Count('id', filter=Q(robot__status__in=['active', 'idle']))
    )

    if all_readings.exists():
        total_active = sum(r['active_readings'] for r in all_readings)
        total_readings = sum(r['total_readings'] for r in all_readings)
        avg_uptime = (total_active / total_readings * 100) if total_readings > 0 else 0
    else:
        # Если нет исторических данных, используем текущий статус
        active_count = robots.filter(status__in=['active', 'idle']).count()
        avg_uptime = (active_count / total_fleet_size * 100) if total_fleet_size > 0 else 0

    avg_uptime = round(avg_uptime, 1)

    # 2. Среднее время работы в часах для активных роботов
    active_robots = robots.filter(status='active')
    average_operational_hours = active_robots.aggregate(
        avg_hours=Coalesce(Avg('operational_hours'), 0, output_field=FloatField())
    )['avg_hours']
    average_operational_hours = round(average_operational_hours, 1)

    # Роботы на обслуживании (только критические и предупреждения)
    critical_robots = robots.filter(status='critical').count()
    warning_robots = robots.filter(status='warning').count()
    robots_needing_maintenance = critical_robots + warning_robots

    # Средний возраст флота (в месяцах)
    fleet_age = 0
    if total_fleet_size > 0:
        total_months = 0
        for robot in robots:
            if robot.created_at:
                delta = timezone.now() - robot.created_at
                months = delta.days // 30
                total_months += months
        fleet_age = round(total_months / total_fleet_size, 1)

    # Получаем группы роботов
    robot_groups = []
    groups = RobotGroup.objects.all().prefetch_related('robots')

    for group in groups:
        group_robots = group.robots.all()
        group_size = group_robots.count()

        # Статистика по статусам
        active_count = group_robots.filter(status='active').count()
        warning_count = group_robots.filter(status='warning').count()
        critical_count = group_robots.filter(status='critical').count()
        maintenance_count = group_robots.filter(status='maintenance').count()

        # Среднее время работы в процентах для группы
        group_readings = RobotReading.objects.filter(
            robot__in=group_robots,
            timestamp__gte=period_start
        ).values('robot_id').annotate(
            total_readings=Count('id'),
            active_readings=Count('id', filter=Q(robot__status__in=['active', 'idle']))
        )

        if group_readings.exists():
            group_total_active = sum(r['active_readings'] for r in group_readings)
            group_total_readings = sum(r['total_readings'] for r in group_readings)
            group_uptime_percent = (group_total_active / group_total_readings * 100) if group_total_readings > 0 else 0
        else:
            group_active_count = group_robots.filter(status__in=['active', 'idle']).count()
            group_uptime_percent = (group_active_count / group_size * 100) if group_size > 0 else 0

        group_uptime_percent = round(group_uptime_percent, 1)

        # Среднее время работы в часах ТОЛЬКО для активных роботов в группе
        active_group_robots = group_robots.filter(status='active')
        if active_group_robots.exists():
            group_uptime_hours = active_group_robots.aggregate(
                avg_hours=Coalesce(Avg('operational_hours'), 0, output_field=FloatField())
            )['avg_hours']
            group_uptime_hours = round(group_uptime_hours, 1)
        else:
            group_uptime_hours = 0.0

        # Добавляем список роботов группы
        robots_in_group = []
        for robot in group_robots:
            robots_in_group.append({
                'id': robot.robot_id,
                'name': robot.name,
                'status': robot.status,
                'status_display': robot.get_status_display(),
                'battery': robot.battery_level,
                'location': robot.location,
                'current_task': robot.current_task
            })

        robot_groups.append({
            'name': group.name,
            'size': group_size,
            'active_count': active_count,
            'warning_count': warning_count,
            'critical_count': critical_count,
            'maintenance_count': maintenance_count,
            'uptime_percent': group_uptime_percent,  # Процент времени работы
            'uptime_hours': group_uptime_hours,  # Часы работы для активных
            'group_type': group.get_group_type_display(),
            'robots': robots_in_group
        })

    context = {
        'avg_uptime': avg_uptime,  # Процент времени работы для всего флота
        'average_operational_hours': average_operational_hours,  # Среднее время в часах
        'total_fleet_size': total_fleet_size,
        'maintenance_needed': robots_needing_maintenance,
        'critical_robots': critical_robots,
        'warning_robots': warning_robots,
        'fleet_age': fleet_age,
        'robot_groups': robot_groups,
        'current_page': 'fleet'
    }

    return render(request, "fleet/fleet.html", context)