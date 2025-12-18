from django.contrib import admin
from django.urls import path, include  # Правильный импорт include

from fleet.views import fleet_view
from diagnostics.views import robot_detail_view
from alerts.views import alerts_view
from reports.views import reports_view
from settings.views import settings_view
from reg.views import regpage
from django.views.defaults import page_not_found
from dashboard.views import dashboard_view, create_test_robots,get_robots_data,update_robots_data  # <-- Исправленный импорт
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('fleet/', fleet_view, name='fleet'),
    path('robot/<str:robot_id>/', robot_detail_view, name='robot_detail'),
    path('reg/', regpage, name='reg'),
    path('create-test-robots/', create_test_robots, name='create_test_robots'),
    path('alerts/', alerts_view, name='alerts'),
    path('reports/', reports_view, name='reports'),
    path('settings/', settings_view, name='settings'),
    path('api/update-robots/', update_robots_data, name='update_robots'),
    path('api/get-robots/', get_robots_data, name='get_robots'),
    path('chat/', include('chat_ai.urls')),  # Теперь работает правильно
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'dashboard.views.custom_404'