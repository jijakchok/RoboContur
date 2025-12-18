from django.shortcuts import render
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from dashboard.models import Robot, Alert, RobotGroup, RobotReading


def reports_view(request):
    # Получение параметров фильтрации
    report_type = request.GET.get('report_type', 'performance')
    group_id = request.GET.get('group_id')
    period = request.GET.get('period', '24h')
    compare = request.GET.get('compare', 'prev')

    # Расчет временных периодов
    now = timezone.now()
    time_ranges = {
        '1h': timedelta(hours=1),
        '10h': timedelta(hours=10),
        '24h': timedelta(days=1),
        '7d': timedelta(days=7),
        '30d': timedelta(days=30),
    }
    period_delta = time_ranges.get(period, timedelta(days=1))
    current_start = now - period_delta

    # Определение предыдущего периода для сравнения
    if compare == 'prev':
        prev_end = current_start
        prev_start = prev_end - period_delta
    elif compare == 'same_last_year':
        prev_end = now - timedelta(days=365)
        prev_start = current_start - timedelta(days=365)
    else:
        prev_start = prev_end = None

    # Фильтрация роботов
    robots = Robot.objects.all()
    if group_id and group_id != '':
        robots = robots.filter(group_id=group_id)

    # Расчет ключевых метрик
    total_robots = robots.count()

    # 1. Средний uptime за выбранный период
    if not robots.exists():
        avg_uptime = 0.0
    else:
        # Получаем все показания за период
        readings = RobotReading.objects.filter(
            robot__in=robots,
            timestamp__gte=current_start
        ).values('robot_id').annotate(
            total_readings=Count('id'),
            active_readings=Count('id', filter=Q(robot__status__in=['active', 'idle']))
        )

        if readings.exists():
            total_active = sum(r['active_readings'] for r in readings)
            total_readings = sum(r['total_readings'] for r in readings)
            avg_uptime = (total_active / total_readings * 100) if total_readings > 0 else 0
        else:
            # Если нет показаний, используем текущий статус
            active_count = robots.filter(status__in=['active', 'idle']).count()
            avg_uptime = (active_count / total_robots * 100) if total_robots > 0 else 0

    # Сравнение с предыдущим периодом
    if prev_start and robots.exists():
        prev_readings = RobotReading.objects.filter(
            robot__in=robots,
            timestamp__gte=prev_start,
            timestamp__lte=prev_end
        ).values('robot_id').annotate(
            total_readings=Count('id'),
            active_readings=Count('id', filter=Q(robot__status__in=['active', 'idle']))
        )

        if prev_readings.exists():
            prev_total_active = sum(r['active_readings'] for r in prev_readings)
            prev_total_readings = sum(r['total_readings'] for r in prev_readings)
            prev_avg_uptime = (prev_total_active / prev_total_readings * 100) if prev_total_readings > 0 else 0
        else:
            prev_active_count = robots.filter(status__in=['active', 'idle']).count()
            prev_avg_uptime = (prev_active_count / total_robots * 100) if total_robots > 0 else 0
    else:
        prev_avg_uptime = avg_uptime

    uptime_change = avg_uptime - prev_avg_uptime
    uptime_change_direction = "up" if uptime_change > 0 else "down" if uptime_change < 0 else "neutral"

    # 2. Задачи, выполненные за период
    tasks_completed = RobotReading.objects.filter(
        robot__in=robots,
        timestamp__gte=current_start,
        timestamp__lte=now
    ).aggregate(
        total_tasks=Sum('active_tasks')
    )['total_tasks'] or 0

    # Сравнение с предыдущим периодом
    if prev_start:
        prev_tasks_completed = RobotReading.objects.filter(
            robot__in=robots,
            timestamp__gte=prev_start,
            timestamp__lte=prev_end
        ).aggregate(
            total_tasks=Sum('active_tasks')
        )['total_tasks'] or 0
    else:
        prev_tasks_completed = tasks_completed

    tasks_change = tasks_completed - prev_tasks_completed
    tasks_change_percent = (tasks_change / prev_tasks_completed * 100) if prev_tasks_completed > 0 else 0
    tasks_change_direction = "up" if tasks_change > 0 else "down" if tasks_change < 0 else "neutral"

    # 3. Энергопотребление
    energy_readings = RobotReading.objects.filter(
        robot__in=robots,
        timestamp__gte=current_start,
        timestamp__lte=now
    ).aggregate(
        avg_cpu=Avg('cpu_load'),
        avg_memory=Avg('memory_usage'),
        reading_count=Count('id')
    )

    avg_cpu = energy_readings['avg_cpu'] or 0
    avg_memory = energy_readings['avg_memory'] or 0
    reading_count = energy_readings['reading_count'] or 1

    # Расчет энергопотребления
    base_consumption = 0.1 * reading_count / 6
    cpu_factor = (avg_cpu / 100) * 0.3 * reading_count / 6
    memory_factor = (avg_memory / 100) * 0.15 * reading_count / 6

    energy_consumption = round(base_consumption + cpu_factor + memory_factor, 1)

    # Сравнение с предыдущим периодом
    if prev_start:
        prev_energy_readings = RobotReading.objects.filter(
            robot__in=robots,
            timestamp__gte=prev_start,
            timestamp__lte=prev_end
        ).aggregate(
            avg_cpu=Avg('cpu_load'),
            avg_memory=Avg('memory_usage'),
            reading_count=Count('id')
        )

        if prev_energy_readings['reading_count'] > 0:
            prev_avg_cpu = prev_energy_readings['avg_cpu'] or 0
            prev_avg_memory = prev_energy_readings['avg_memory'] or 0
            prev_reading_count = prev_energy_readings['reading_count']

            prev_base = 0.1 * prev_reading_count / 6
            prev_cpu_factor = (prev_avg_cpu / 100) * 0.3 * prev_reading_count / 6
            prev_memory_factor = (prev_avg_memory / 100) * 0.15 * prev_reading_count / 6

            prev_energy_consumption = prev_base + prev_cpu_factor + prev_memory_factor
        else:
            prev_energy_consumption = energy_consumption
    else:
        prev_energy_consumption = energy_consumption

    energy_change = energy_consumption - prev_energy_consumption
    energy_change_percent = (energy_change / prev_energy_consumption * 100) if prev_energy_consumption > 0 else 0
    energy_change_direction = "down" if energy_change < 0 else "up" if energy_change > 0 else "neutral"

    # 4. Дополнительные метрики
    avg_battery = robots.aggregate(avg=Avg('battery_level'))['avg'] or 0
    avg_battery = round(avg_battery, 1)

    avg_temperature = robots.aggregate(avg=Avg('temperature'))['avg'] or 0
    avg_temperature = round(avg_temperature, 1)

    # Роботы с высокой температурой
    high_temp_count = robots.filter(temperature__gt=45).count()

    # Группы роботов - ИСПРАВЛЕНО: используем другое имя для аннотации
    all_groups = RobotGroup.objects.annotate(robots_count=Count('robots'))

    # Данные для групп
    groups_data = []
    for group in all_groups:
        group_robots = group.robots.all()
        if not group_robots.exists():
            continue

        # Расчет uptime для группы
        group_readings = RobotReading.objects.filter(
            robot__in=group_robots,
            timestamp__gte=current_start
        ).values('robot_id').annotate(
            total_readings=Count('id'),
            active_readings=Count('id', filter=Q(robot__status__in=['active', 'idle']))
        )

        if group_readings.exists():
            group_total_active = sum(r['active_readings'] for r in group_readings)
            group_total_readings = sum(r['total_readings'] for r in group_readings)
            group_uptime = (group_total_active / group_total_readings * 100) if group_total_readings > 0 else 0
        else:
            group_active_count = group_robots.filter(status__in=['active', 'idle']).count()
            group_uptime = (group_active_count / group_robots.count() * 100) if group_robots.count() > 0 else 0

        # Средние значения
        group_avg_battery = group_robots.aggregate(avg=Avg('battery_level'))['avg'] or 0
        group_avg_temperature = group_robots.aggregate(avg=Avg('temperature'))['avg'] or 0

        # Количество алертов
        group_alerts_count = Alert.objects.filter(
            robot__in=group_robots,
            resolved=False,
            created_at__gte=current_start
        ).count()

        # Расчет энергопотребления для группы
        group_energy_readings = RobotReading.objects.filter(
            robot__in=group_robots,
            timestamp__gte=current_start
        ).aggregate(
            avg_cpu=Avg('cpu_load'),
            avg_memory=Avg('memory_usage'),
            reading_count=Count('id')
        )

        group_energy = 0
        if group_energy_readings['reading_count'] > 0:
            g_avg_cpu = group_energy_readings['avg_cpu'] or 0
            g_avg_memory = group_energy_readings['avg_memory'] or 0
            g_count = group_energy_readings['reading_count']

            g_base = 0.1 * g_count / 6
            g_cpu_factor = (g_avg_cpu / 100) * 0.3 * g_count / 6
            g_memory_factor = (g_avg_memory / 100) * 0.15 * g_count / 6

            group_energy = round(g_base + g_cpu_factor + g_memory_factor, 1)

        groups_data.append({
            'id': group.id,
            'name': group.name,
            'robots_count': group_robots.count(),
            'uptime': round(group_uptime, 1),
            'avg_battery': round(group_avg_battery, 1),
            'avg_temperature': round(group_avg_temperature, 1),
            'alerts_count': group_alerts_count,
            'energy_consumption': group_energy,
            'group_type': group.group_type,
            'get_group_type_display': group.get_group_type_display(),
        })

    # Подготовка данных для статистики (без графиков)
    context = {
        'current_page': 'reports',
        'avg_uptime': round(avg_uptime, 1),
        'uptime_change': round(abs(uptime_change), 1),
        'uptime_change_direction': uptime_change_direction,
        'tasks_completed': tasks_completed,
        'tasks_change_percent': round(abs(tasks_change_percent), 1),
        'tasks_change_direction': tasks_change_direction,
        'energy_consumption': energy_consumption,
        'energy_change_percent': round(abs(energy_change_percent), 1),
        'energy_change_direction': energy_change_direction,
        'avg_battery': avg_battery,
        'avg_temperature': avg_temperature,
        'high_temp_count': high_temp_count,
        'groups_data': groups_data,
        'all_groups': all_groups,  # Теперь используем robots_count вместо robot_count
        'total_robots': total_robots,
        'battery_colors': {
            'critical': '#D32F2F',
            'warning': '#FFC107',
            'normal': '#4CAF50'
        },
        'critical_energy_threshold': 50,
    }

    return render(request, "reports/reports.html", context)