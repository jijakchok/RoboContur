
from django.db import models
from django.contrib.auth.models import User


class Robot(models.Model):
    """Основная модель для хранения данных о роботах"""

    # Типы роботов
    ROBOT_TYPES = (
        ('warehouse', 'Складской'),
        ('production', 'Производственный'),
        ('delivery', 'Доставки'),
        ('inspection', 'Инспекционный'),
        ('cleaning', 'Уборки'),
        ('security', 'Безопасности'),
    )

    # Статусы роботов
    STATUS_CHOICES = (
        ('active', 'Активен'),
        ('idle', 'Простой'),
        ('warning', 'Предупреждение'),
        ('critical', 'Критический'),
        ('maintenance', 'На обслуживании'),
        ('offline', 'Офлайн'),
    )

    # Основные поля
    robot_id = models.CharField(max_length=50, unique=True, verbose_name="ID робота")
    name = models.CharField(max_length=100, verbose_name="Название")
    robot_type = models.CharField(max_length=20, choices=ROBOT_TYPES, default='warehouse', verbose_name="Тип")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")

    # Технические параметры
    battery_level = models.FloatField(default=100.0, verbose_name="Заряд батареи (%)")
    temperature = models.FloatField(default=25.0, verbose_name="Температура (°C)")
    cpu_load = models.FloatField(default=0.0, verbose_name="Загрузка CPU (%)")
    memory_usage = models.FloatField(default=0.0, verbose_name="Использование памяти (%)")

    # Местоположение и задачи
    location = models.CharField(max_length=100, verbose_name="Местоположение")
    current_task = models.CharField(max_length=200, blank=True, null=True, verbose_name="Текущая задача")
    assigned_tasks = models.IntegerField(default=0, verbose_name="Всего задач")

    # Статистика и время
    operational_hours = models.FloatField(default=0.0, verbose_name="Часов в работе")
    last_maintenance = models.DateTimeField(null=True, blank=True, verbose_name="Последнее обслуживание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    # Связи
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='robots', verbose_name="Владелец")
    group = models.ForeignKey('RobotGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='robots',
                              verbose_name="Группа")

    class Meta:
        verbose_name = "Робот"
        verbose_name_plural = "Роботы"
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['robot_type']),
            models.Index(fields=['battery_level']),
        ]

    def __str__(self):
        return f"{self.name} ({self.robot_id})"

    @property
    def is_active(self):
        """Проверка, активен ли робот"""
        return self.status in ['active', 'idle', 'warning']

    @property
    def needs_attention(self):
        """Проверка, требует ли робот внимания"""
        return self.status in ['warning', 'critical'] or self.battery_level < 30 or self.temperature > 45

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status  # Сохраняем исходный статус при загрузке

    def save(self, *args, **kwargs):
        # Проверяем, изменился ли статус
        status_changed = hasattr(self, '_original_status') and self._original_status != self.status

        super().save(*args, **kwargs)

        # Если статус изменился, создаем алерт
        if status_changed:
            self.create_alert_for_status_change()
            self._original_status = self.status  # Обновляем исходный статус

    def create_alert_for_status_change(self):
        """Создает алерт при изменении статуса на проблемный"""
        alert_type = None
        alert_title = ""
        alert_description = ""

        # Определяем тип алерта в зависимости от статуса
        if self.status == 'critical':
            alert_type = 'critical'
            alert_title = f"Критический статус - {self.robot_id}"
            alert_description = f"Робот {self.name} перешел в критический статус: {self.get_status_display()}"
        elif self.status == 'warning':
            alert_type = 'warning'
            alert_title = f"Предупреждение - {self.robot_id}"
            alert_description = f"Робот {self.name} перешел в режим предупреждения: {self.get_status_display()}"
        elif self.status == 'maintenance':
            alert_type = 'maintenance'
            alert_title = f"Обслуживание - {self.robot_id}"
            alert_description = f"Робот {self.name} переведен на обслуживание: {self.get_status_display()}"

        # Создаем алерт, если тип определен и нет активного алерта этого типа
        if alert_type:
            # Проверяем, нет ли уже активного алерта этого типа
            existing_alert = Alert.objects.filter(
                robot=self,
                alert_type=alert_type,
                resolved=False
            ).exists()

            if not existing_alert:
                Alert.objects.create(
                    robot=self,
                    alert_type=alert_type,
                    title=alert_title,
                    description=alert_description,
                    resolved=False
                )


class Alert(models.Model):
    """Модель для хранения оповещений о состоянии роботов"""

    ALERT_TYPES = (
        ('critical', 'Критическое'),
        ('warning', 'Предупреждение'),
        ('maintenance', 'Обслуживание'),
        ('info', 'Информационное'),
    )

    SEVERITY_LEVELS = (
        (1, 'Низкий'),
        (2, 'Средний'),
        (3, 'Высокий'),
        (4, 'Критический'),
    )

    robot = models.ForeignKey(Robot, on_delete=models.CASCADE, related_name='alerts', verbose_name="Робот")
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='warning', verbose_name="Тип оповещения")
    severity = models.IntegerField(choices=SEVERITY_LEVELS, default=2, verbose_name="Уровень серьезности")

    title = models.CharField(max_length=100, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    resolved = models.BooleanField(default=False, verbose_name="Решено")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Время решения")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Инициатор")

    # Параметры, вызвавшие оповещение
    trigger_value = models.FloatField(null=True, blank=True, verbose_name="Значение триггера")
    threshold_value = models.FloatField(null=True, blank=True, verbose_name="Пороговое значение")

    class Meta:
        verbose_name = "Оповещение"
        verbose_name_plural = "Оповещения"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resolved', 'alert_type']),
            models.Index(fields=['robot', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.robot.name}: {self.title}"

    def resolve(self, user=None):
        """Метод для решения оповещения"""
        self.resolved = True
        self.resolved_at = timezone.now()
        self.triggered_by = user
        self.save()

    def resolve_alerts_on_status_normal(self):
        """Закрывает алерты при возврате в нормальный статус"""
        if self.status in ['active', 'idle', 'offline']:
            # Закрываем все активные алерты для этого робота
            Alert.objects.filter(
                robot=self,
                resolved=False
            ).update(
                resolved=True,
                resolved_at=timezone.now()
            )

    def save(self, *args, **kwargs):
        status_changed = hasattr(self, '_original_status') and self._original_status != self.status

        super().save(*args, **kwargs)

        if status_changed:
            # Если статус стал нормальным, закрываем алерты
            if self.status in ['active', 'idle', 'offline']:
                self.resolve_alerts_on_status_normal()
            else:
                # Иначе создаем новый алерт
                self.create_alert_for_status_change()

            self._original_status = self.status


class RobotGroup(models.Model):
    """Модель для группировки роботов"""

    GROUP_TYPES = (
        ('location', 'По местоположению'),
        ('function', 'По функциям'),
        ('priority', 'По приоритету'),
        ('custom', 'Пользовательская'),
    )

    name = models.CharField(max_length=100, verbose_name="Название группы")
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES, default='custom', verbose_name="Тип группы")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='robot_groups', verbose_name="Владелец")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    # Настройки мониторинга для группы
    alert_threshold = models.FloatField(default=40.0, verbose_name="Порог оповещения (%)")
    maintenance_schedule = models.CharField(max_length=100, blank=True, null=True, verbose_name="График обслуживания")

    class Meta:
        verbose_name = "Группа роботов"
        verbose_name_plural = "Группы роботов"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def robot_count(self):
        """Количество роботов в группе"""
        return self.robots.count()

    @property
    def active_robots_count(self):
        """Количество активных роботов в группе"""
        return self.robots.filter(status__in=['active', 'idle']).count()


class Report(models.Model):
    """Модель для хранения отчетов"""

    REPORT_TYPES = (
        ('daily', 'Ежедневный'),
        ('weekly', 'Еженедельный'),
        ('monthly', 'Ежемесячный'),
        ('custom', 'Пользовательский'),
        ('alert_summary', 'Сводка по оповещениям'),
        ('performance', 'Производительность'),
        ('maintenance', 'Обслуживание'),
    )

    TIME_PERIODS = (
        ('today', 'Сегодня'),
        ('yesterday', 'Вчера'),
        ('last_7_days', 'Последние 7 дней'),
        ('last_30_days', 'Последние 30 дней'),
        ('this_month', 'Этот месяц'),
        ('last_month', 'Прошлый месяц'),
        ('custom', 'Выбрать период'),
    )

    title = models.CharField(max_length=200, verbose_name="Заголовок отчета")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='daily', verbose_name="Тип отчета")
    time_period = models.CharField(max_length=20, choices=TIME_PERIODS, default='today', verbose_name="Период")

    # Связи
    robot_group = models.ForeignKey(RobotGroup, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reports', verbose_name="Группа роботов")
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', verbose_name="Создал")

    # Период для пользовательских отчетов
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="Начало периода")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Конец периода")

    # Данные отчета
    report_data = models.JSONField(verbose_name="Данные отчета")
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Сгенерирован")

    # Метаданные
    file_format = models.CharField(max_length=10, default='pdf', verbose_name="Формат файла")
    file_path = models.CharField(max_length=255, blank=True, null=True, verbose_name="Путь к файлу")
    is_archived = models.BooleanField(default=False, verbose_name="Архивирован")

    class Meta:
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', '-generated_at']),
            models.Index(fields=['robot_group', '-generated_at']),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} отчет: {self.title}"

    def generate_report_data(self):
        """Генерация данных отчета на основе выбранных параметров"""
        from django.utils import timezone
        from datetime import timedelta

        # Определение периода
        now = timezone.now()
        if self.time_period == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif self.time_period == 'yesterday':
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        elif self.time_period == 'last_7_days':
            start = now - timedelta(days=7)
            end = now
        elif self.time_period == 'last_30_days':
            start = now - timedelta(days=30)
            end = now
        elif self.time_period == 'custom' and self.start_date and self.end_date:
            start = self.start_date
            end = self.end_date
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now

        # Фильтрация роботов
        robots = Robot.objects.filter(owner=self.generated_by)
        if self.robot_group:
            robots = robots.filter(group=self.robot_group)

        # Сбор статистики
        stats = {
            'total_robots': robots.count(),
            'active_robots': robots.filter(status__in=['active', 'idle']).count(),
            'maintenance_robots': robots.filter(status='maintenance').count(),
            'critical_alerts': Alert.objects.filter(
                robot__in=robots,
                alert_type='critical',
                resolved=False,
                created_at__range=(start, end)
            ).count(),
            'warning_alerts': Alert.objects.filter(
                robot__in=robots,
                alert_type='warning',
                resolved=False,
                created_at__range=(start, end)
            ).count(),
            'maintenance_alerts': Alert.objects.filter(
                robot__in=robots,
                alert_type='maintenance',
                resolved=False,
                created_at__range=(start, end)
            ).count(),
            'avg_battery': robots.aggregate(models.Avg('battery_level'))['battery_level__avg'] or 0,
            'avg_temperature': robots.aggregate(models.Avg('temperature'))['temperature__avg'] or 0,
            'most_active_location': robots.values('location').annotate(count=models.Count('id')).order_by(
                '-count').first()
        }

        # Добавление деталей по роботам для подробных отчетов
        if self.report_type in ['performance', 'maintenance']:
            robot_details = []
            for robot in robots:
                robot_details.append({
                    'id': robot.robot_id,
                    'name': robot.name,
                    'status': robot.get_status_display(),
                    'battery': robot.battery_level,
                    'temperature': robot.temperature,
                    'location': robot.location,
                    'current_task': robot.current_task,
                    'alerts_count': Alert.objects.filter(robot=robot, created_at__range=(start, end)).count()
                })
            stats['robot_details'] = robot_details

        return stats


class RobotReading(models.Model):
    """Модель для хранения исторических показаний с датчиков роботов"""

    robot = models.ForeignKey(Robot, on_delete=models.CASCADE, related_name='readings', verbose_name="Робот")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время показания")

    # Данные с датчиков
    temperature = models.FloatField(verbose_name="Температура (°C)")
    battery_level = models.FloatField(verbose_name="Уровень заряда (%)")
    cpu_load = models.FloatField(verbose_name="Загрузка CPU (%)")
    memory_usage = models.FloatField(verbose_name="Использование памяти (%)")
    location_x = models.FloatField(default=0.0, verbose_name="Координата X")
    location_y = models.FloatField(default=0.0, verbose_name="Координата Y")
    active_tasks = models.IntegerField(default=0, verbose_name="Активные задачи")

    # Дополнительные параметры
    signal_strength = models.FloatField(null=True, blank=True, verbose_name="Сила сигнала")
    error_count = models.IntegerField(default=0, verbose_name="Количество ошибок")

    class Meta:
        verbose_name = "Показание датчиков"
        verbose_name_plural = "Показания датчиков"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['robot', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"Показания для {self.robot.name} от {self.timestamp.strftime('%Y-%m-%d %H:%M')}"