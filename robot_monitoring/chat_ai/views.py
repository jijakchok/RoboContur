from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.db.models import Avg
from dashboard.models import Robot, Alert


def chat_ai(request):
    """Представление для отображения страницы чата"""
    return render(request, 'chat_ai/chat_ai.html')


def get_robots_data():
    """Получает данные о роботах из базы данных"""
    try:
        robots = Robot.objects.all()

        if not robots.exists():
            return [
                {
                    "id": "TEST-001",
                    "name": "Тестовый робот",
                    "status": "active",
                    "battery": 90.0,
                    "temperature": 30.0,
                    "location": "Тестовая зона",
                    "task": "Тестовая задача",
                    "robot_type": "warehouse"
                }
            ]

        robots_data = []
        for robot in robots:
            # Получаем последнее оповещение для робота
            last_alert = Alert.objects.filter(robot=robot, resolved=False).order_by('-created_at').first()

            robots_data.append({
                "id": robot.robot_id,
                "name": robot.name,
                "status": robot.status,
                "battery": robot.battery_level,
                "temperature": robot.temperature,
                "location": robot.location,
                "task": robot.current_task or "Без задачи",
                "robot_type": robot.robot_type,
                "last_alert": {
                    "type": last_alert.alert_type if last_alert else None,
                    "title": last_alert.title if last_alert else None,
                    "description": last_alert.description if last_alert else None,
                    "time": last_alert.created_at.strftime("%Y-%m-%d %H:%M") if last_alert else None
                } if last_alert else None
            })

        return robots_data

    except Exception as e:
        print(f"Ошибка при получении данных роботов: {e}")
        return [
            {
                "id": "ERROR-001",
                "name": "Ошибка получения данных",
                "status": "critical",
                "battery": 0,
                "temperature": 0,
                "location": "Неизвестно",
                "task": "Невозможно получить данные из БД",
                "robot_type": "warehouse"
            }
        ]


def format_robots_context(robots_data):
    """Форматирует данные роботов в понятный контекст для нейросети"""
    if not robots_data:
        return "Нет данных о роботах."

    context = "Данные по всем роботам:\n\n"

    for robot in robots_data:
        status_display = "Активен" if robot['status'] == 'active' else "Требует внимания" if robot['status'] in [
            'warning', 'maintenance'] else "Критический"

        context += f"Робот: {robot['name']} (ID: {robot['id']})\n"
        context += f"- Статус: {status_display}\n"
        context += f"- Тип: {robot['robot_type']}\n"
        context += f"- Заряд батареи: {robot['battery']}%\n"
        context += f"- Температура: {robot['temperature']}°C\n"
        context += f"- Местоположение: {robot['location']}\n"
        context += f"- Текущая задача: {robot['task']}\n"

        if robot.get('last_alert') and robot['last_alert']:
            context += f"- Последнее оповещение: {robot['last_alert']['title']} ({robot['last_alert']['type']})\n"
            context += f"  Описание: {robot['last_alert']['description']}\n"
            context += f"  Время: {robot['last_alert']['time']}\n"

        context += "\n"

    # Добавляем сводную статистику
    avg_battery = sum(r['battery'] for r in robots_data) / len(robots_data)
    avg_temp = sum(r['temperature'] for r in robots_data) / len(robots_data)
    critical_robots = sum(1 for r in robots_data if r['status'] == 'critical')
    warning_robots = sum(1 for r in robots_data if r['status'] == 'warning')
    maintenance_robots = sum(1 for r in robots_data if r['status'] == 'maintenance')

    context += f"Сводная статистика:\n"
    context += f"- Всего роботов: {len(robots_data)}\n"
    context += f"- Активных: {len(robots_data) - critical_robots - warning_robots - maintenance_robots}\n"
    context += f"- Критических: {critical_robots}\n"
    context += f"- С предупреждениями: {warning_robots}\n"
    context += f"- На обслуживании: {maintenance_robots}\n"
    context += f"- Средний заряд батареи: {avg_battery:.1f}%\n"
    context += f"- Средняя температура: {avg_temp:.1f}°C\n"

    return context


def call_hf_api(user_message, robot_context):
    """Выполняет запрос к Hugging Face API с правильным URL"""
    # Токен Hugging Face
    HF_TOKEN = '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'

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    # Формируем полный запрос с контекстом
    full_message = (
        f"Отвечай только на русском языке.Не используй НИКАКИХ средств выделения. Пользователь спрашивает: {user_message}\n\n"
        f"Контекст по роботам:\n{robot_context}\n\n"
        f"Пожалуйста, дай краткий, но информативный ответ. Если вопрос требует детального ответа, структурируй его по пунктам. "
        f"Всегда учитывай контекст по роботам при ответе."
    )

    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "user", "content": full_message}
        ],
        "max_tokens": 350,
        "temperature": 0.4
    }

    try:
        # ИСПРАВЛЕННЫЙ URL для chat completions
        response = requests.post(
            "https://router.huggingface.co/v1/chat/completions",  # Правильный URL
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                response_text = result["choices"][0]["message"]["content"]
                return {'success': True, 'response': response_text}
            return {'success': False, 'error': 'Некорректный формат ответа API'}
        else:
            error_msg = response.text[:500]  # Ограничим длину ошибки
            return {
                'success': False,
                'error': f'Ошибка API: {response.status_code}. {error_msg}'
            }

    except Exception as e:
        print(f"Ошибка: {e}")
        return {
            'success': False,
            'error': f"Ошибка при обращении к API: {str(e)}"
        }


@csrf_exempt
def evaluate_all_robots(request):
    """Представление для оценки состояния всех роботов"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST запросы разрешены'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')

        # Получаем данные о роботах
        robot_data = get_robots_data()

        # Формируем контекст для запроса
        robot_context = format_robots_context(robot_data)

        # Вызываем API
        api_response = call_hf_api(user_message, robot_context)

        return JsonResponse(api_response)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def test_api_connection(request):
    """Тестовое представление для проверки соединения с API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST запросы разрешены'}, status=405)

    try:
        # Тестовый запрос к API
        HF_TOKEN = "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"
        headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}

        payload = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [{"role": "user", "content": "Привет! Это тестовый запрос."}],
            "max_tokens": 50
        }

        response = requests.post(
            "https://router.huggingface.co/v1/chat/completions ",
            headers=headers,
            json=payload,
            timeout=30
        )

        return JsonResponse({
            'status': 'success',
            'api_status': response.status_code,
            'response': response.json() if response.status_code == 200 else response.text
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })