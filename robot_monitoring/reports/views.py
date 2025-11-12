from django.shortcuts import render

def reports_view(request):
    return render(request, "reports/reports.html")