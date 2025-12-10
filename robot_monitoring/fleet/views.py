from django.shortcuts import render
from dashboard.models import Robot, RobotGroup
from django.db.models import Count, Avg, Q


def fleet_view(request):
    # Получаем все роботы
    robots = Robot.objects.all()

    # Общие метрики
    total_fleet_size = robots.count()

    # Среднее время работы (operational_hours)
    average_uptime = robots.aggregate(avg_uptime=Avg('operational_hours'))['avg_uptime'] or 0
    average_uptime = round(average_uptime, 1)

    # Роботы на обслуживании
    maintenance_needed = robots.filter(status='maintenance').count()

    # Средний возраст флота (в месяцах)
    fleet_age = 0
    if total_fleet_size > 0:
        from django.utils import timezone
        from datetime import timedelta
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
        active_count = group_robots.filter(status__in=['active', 'idle']).count()
        warning_count = group_robots.filter(status='warning').count()
        critical_count = group_robots.filter(status='critical').count()
        maintenance_count = group_robots.filter(status='maintenance').count()

        # Среднее время работы для группы
        group_uptime = group_robots.aggregate(avg_uptime=Avg('operational_hours'))['avg_uptime'] or 0
        group_uptime = round(group_uptime, 1)

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
            'uptime': group_uptime,
            'group_type': group.get_group_type_display(),
            'robots': robots_in_group
        })

    context = {
        'total_fleet_size': total_fleet_size,
        'average_uptime': average_uptime,
        'maintenance_needed': maintenance_needed,
        'fleet_age': fleet_age,
        'robot_groups': robot_groups,
        'current_page': 'fleet'
    }

    return render(request, "fleet/fleet.html", context)