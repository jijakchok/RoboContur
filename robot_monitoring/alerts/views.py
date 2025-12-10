from django.shortcuts import render

from dashboard.models import Robot, Alert


def alerts_view(request):
    # Получаем все активные алерты (не решенные)
    active_alerts = Alert.objects.filter(resolved=False).select_related('robot').order_by('-created_at')

    # Фильтруем алерты по типам
    critical_alerts = active_alerts.filter(alert_type='critical')
    warning_alerts = active_alerts.filter(alert_type='warning')
    maintenance_alerts = active_alerts.filter(alert_type='maintenance')

    # Получаем список всех роботов для фильтра
    robots = Robot.objects.all().order_by('name')

    context = {
        'critical_alerts': critical_alerts,
        'warning_alerts': warning_alerts,
        'maintenance_alerts': maintenance_alerts,
        'robots': robots,
        'current_page': 'alerts'
    }

    return render(request, "alerts/alerts.html", context)