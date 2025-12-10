from .models import Robot, RobotGroup, Alert
from chat_ai.views import get_robots_data, Robot as ChatRobot
from django.db.models import Count, Avg

def get_dashboard_data(use_test_data=False):
    """Получает данные для дашборда, используя тестовые данные при необходимости"""

    if use_test_data or ChatRobot is None:
        # Используем тестовые данные
        robots_data = get_robots_data()

        # Группируем роботов по группам
        groups = {}
        for robot in robots_data:
            group_name = robot.get('group', 'Без группы')
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(robot)

        # Формируем данные для дашборда
        total_robots = len(robots_data)
        active_robots = sum(1 for r in robots_data if r['status'] in ['active', 'idle'])
        maintenance_robots = sum(1 for r in robots_data if r['status'] == 'maintenance')

        critical_alerts = sum(1 for r in robots_data if r['status'] == 'critical')
        warning_alerts = sum(1 for r in robots_data if r['status'] == 'warning')

        # Статистика по местоположениям
        location_stats = {}
        for robot in robots_data:
            loc = robot['location']
            if loc not in location_stats:
                location_stats[loc] = {'count': 0, 'battery_sum': 0, 'temp_sum': 0}

            location_stats[loc]['count'] += 1
            location_stats[loc]['battery_sum'] += robot['battery']
            location_stats[loc]['temp_sum'] += robot['temperature']

        location_stats_list = []
        for loc, data in location_stats.items():
            location_stats_list.append({
                'location': loc,
                'count': data['count'],
                'avg_battery': data['battery_sum'] / data['count'],
                'avg_temperature': data['temp_sum'] / data['count']
            })

        # Группы
        robot_groups = [
            {'name': group_name, 'count': len(robots), 'robots': robots}
            for group_name, robots in groups.items()
        ]

        return {
            'robots': robots_data,
            'total_robots': total_robots,
            'active_robots': active_robots,
            'maintenance_robots': maintenance_robots,
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'maintenance_alerts': maintenance_robots,  # Используем maintenance_robots для обслуживания
            'robot_groups': robot_groups,
            'recent_robots': robots_data[:5],
            'location_stats': location_stats_list,
            'is_test_data': True
        }

    # Используем реальные данные из базы
    robots = Robot.objects.all()
    total_robots = robots.count()
    active_robots = robots.filter(status__in=['active', 'idle']).count()
    maintenance_robots = robots.filter(status='maintenance').count()

    # Данные по оповещениям
    critical_alerts = Alert.objects.filter(alert_type='critical', resolved=False).count()
    warning_alerts = Alert.objects.filter(alert_type='warning', resolved=False).count()
    maintenance_alerts = Alert.objects.filter(alert_type='maintenance', resolved=False).count()

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

    return {
        'robots': robots,
        'total_robots': total_robots,
        'active_robots': active_robots,
        'maintenance_robots': maintenance_robots,
        'critical_alerts': critical_alerts,
        'warning_alerts': warning_alerts,
        'maintenance_alerts': maintenance_alerts,
        'robot_groups': robot_groups,
        'recent_robots': recent_robots,
        'location_stats': location_stats,
        'is_test_data': False
    }