from django.shortcuts import render


def monitoring_view(request):
    robots = [
        {
            "id": "RB-001",
            "name": "AssemblyBot 1",
            "status": "Active",
            "temperature": "42°C",
            "battery": 85,
            "signal": "Strong",
            "last_update": "1 min ago"
        },
        {
            "id": "RB-002",
            "name": "DeliveryBot 1",
            "status": "Active",
            "temperature": "38°C",
            "battery": 72,
            "signal": "Medium",
            "last_update": "2 mins ago"
        },
        {
            "id": "RB-003",
            "name": "WelderBot 2",
            "status": "Warning",
            "temperature": "78°C",
            "battery": 28,
            "signal": "Weak",
            "last_update": "3 mins ago"
        },
    ]

    metrics = {
        "uptime": "92%",
        "task_completion": "88%",
        "error_rate": "3%",
    }

    return render(request, "monitoring/monitoring.html", {
        "robots": robots,
        "metrics": metrics,
    })