from django.contrib import admin

from django.contrib import admin
from .models import Robot, Alert, RobotGroup, Report, RobotReading

# Регистрация модели Robot
@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    list_display = ('robot_id', 'name', 'robot_type', 'status', 'battery_level', 'temperature', 'location')
    list_filter = ('status', 'robot_type', 'location')
    search_fields = ('robot_id', 'name', 'location')
    fieldsets = (
        ('Основная информация', {
            'fields': ('robot_id', 'name', 'robot_type', 'status', 'owner')
        }),
        ('Технические параметры', {
            'fields': ('battery_level', 'temperature', 'cpu_load', 'memory_usage')
        }),
        ('Местоположение и задачи', {
            'fields': ('location', 'current_task', 'assigned_tasks', 'group')
        }),
    )

# Регистрация других моделей
admin.site.register(Alert)
admin.site.register(RobotGroup)
admin.site.register(Report)
admin.site.register(RobotReading)