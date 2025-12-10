from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_ai, name='chat'),
    path('api/evaluate-all-robots/', views.evaluate_all_robots, name='evaluate_all_robots'),
    path('api/test-connection/', views.test_api_connection, name='test_api_connection'),
]