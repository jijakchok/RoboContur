from django.shortcuts import render

def robot_detail_view(request, robot_id):
    # Пока используем статические данные для демонстрации
    robot = {
        "id": robot_id,
        "name": f"Robot-{robot_id}",
        "status": "Active",
        "battery": 75,
        "location": "Warehouse Zone A",
        "task": "Material Transport",
        "temperature": "38°C",
        "uptime": "5h 23m",
        "last_maintenance": "2023-10-15"
    }
    return render(request, "diagnostics/robot_detail.html", {"robot": robot})