from django.shortcuts import render

def dashboard_view(request):
    robots = [
        {"id": 1, "name": "Robot-A", "status": "Активен", "color": "green"},
        {"id": 2, "name": "Robot-B", "status": "Ошибка", "color": "red"},
        {"id": 3, "name": "Robot-C", "status": "В простое", "color": "yellow"},
    ]
    stats = {
        "total": len(robots),
        "active": 1,
        "idle": 1,
        "error": 1,
    }
    return render(request, "dashboard/dashboard.html", {"robots": robots, "stats": stats})