from django.shortcuts import render

def control_view(request):
    """
    Общий вид управления для всех роботов
    """
    return render(request, "control/robot_control.html")

def robot_control_view(request, robot_id):
    """
    Управление конкретным роботом по ID
    """
    robot = {
        "id": robot_id,
        "name": f"Robot-{robot_id}",
        "status": "Active",
        "battery": 75,
        "location": "Warehouse Zone A",
        "task": "Material Transport"
    }
    return render(request, "control/robot_control.html", {"robot": robot})