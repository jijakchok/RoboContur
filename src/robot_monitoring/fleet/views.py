from django.shortcuts import render

def fleet_view(request):
    robots = [
        {
            "id": "RB-001",
            "name": "AssemblyBot 1",
            "type": "Manipulator",
            "status": "Active",
            "battery": 85,
            "location": "Assembly Line A",
            "task": "Part Assembly"
        },
        {
            "id": "RB-002",
            "name": "DeliveryBot 1",
            "type": "Mobile",
            "status": "Active",
            "battery": 72,
            "location": "Warehouse",
            "task": "Inventory Move"
        },
        {
            "id": "RB-003",
            "name": "WelderBot 2",
            "type": "Specialized",
            "status": "Warning",
            "battery": 28,
            "location": "Welding Station",
            "task": "Component Welding"
        },
        {
            "id": "RB-004",
            "name": "InspectoBot 1",
            "type": "Drone",
            "status": "Critical",
            "battery": 12,
            "location": "Storage Area 3",
            "task": "Inventory Scan"
        },
    ]
    return render(request, "fleet/fleet.html", {"robots": robots})