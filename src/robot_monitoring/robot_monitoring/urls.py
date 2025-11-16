from django.contrib import admin
from django.urls import path

from dashboard.views import dashboard_view
from monitoring.views import monitoring_view  # Добавьте этот импорт
from control.views import control_view
from fleet.views import fleet_view
from diagnostics.views import robot_detail_view
from alerts.views import alerts_view
from reports.views import reports_view
from settings.views import settings_view

from control.views import robot_control_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('monitoring/', monitoring_view, name='monitoring'),  # Добавьте эту строку
    path('control/', control_view, name='control'),
    path('fleet/', fleet_view, name='fleet'),
    path('robot/<str:robot_id>/', robot_detail_view, name='robot_detail'),

    path('alerts/', alerts_view, name='alerts'),
    path('reports/', reports_view, name='reports'),
    path('settings/', settings_view, name='settings'),
    path('control/', control_view, name='control'),
    path('control/<str:robot_id>/', robot_control_view, name='robot_control'),
]