from django.shortcuts import render

def alerts_view(request):
    alerts = [
        {"id": 1, "robot": "Robot-A", "type": "CRITICAL", "description": "Перегрев", "time": "14:23:45"},
        {"id": 2, "robot": "Robot-B", "type": "WARNING", "description": "Низкий заряд", "time": "14:22:12"},
        {"id": 3, "robot": "Robot-C", "type": "INFO", "description": "Задача завершена", "time": "14:20:33"},
    ]
    return render(request, "alerts/alerts.html", {"alerts": alerts})