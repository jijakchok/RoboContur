from django.shortcuts import render, get_object_or_404
from dashboard.models import Robot, Alert


def robot_detail_view(request, robot_id):
    # Получаем робота из базы данных
    robot = get_object_or_404(Robot, robot_id=robot_id)

    # Получаем алерты, связанные с этим роботом
    alerts = Alert.objects.filter(robot=robot, resolved=False).order_by('-created_at')

    context = {
        'robot': robot,
        'alerts': alerts
    }

    return render(request, "diagnostics/robot_detail.html", context)