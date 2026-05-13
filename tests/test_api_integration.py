"""
Интеграционные тесты API через HTTP запросы.
Проверяют полный цикл работы с задачами через FastAPI сервер.
Требуют запущенного сервера: uvicorn app.main:app --port 8000
"""
import pytest
import httpx
import os
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


# Базовый URL API (должен быть запущен сервер)
API_BASE_URL = os.getenv('TEST_API_URL', 'http://localhost:8000')
TIMEOUT_SECONDS = 30


@pytest.fixture(scope='module')
def api_client():
    """HTTP клиент для API тестов."""
    with httpx.Client(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        yield client


class TestHealthCheck:
    """Тесты проверки доступности сервиса."""
    
    def test_health_endpoint(self, api_client):
        """Проверка health check endpoint."""
        try:
            response = api_client.get('/health')
            assert response.status_code == 200
            
            data = response.json()
            assert data['status'] == 'ok'
            assert 'service' in data
            assert 'version' in data
            
            print(f"\n✅ Health check: {data}")
        except httpx.ConnectError as e:
            pytest.fail(
                f"❌ Не удалось подключиться к API по адресу {API_BASE_URL}. "
                f"Убедитесь, что сервер запущен: uvicorn app.main:app --port 8000\n"
                f"Ошибка: {e}"
            )


class TestParseEndpoint:
    """Тесты эндпоинта парсинга ссылок."""
    
    def test_parse_yandex_links(self, api_client, test_parse_data):
        """Парсинг ссылок Яндекс.Диск через API."""
        text = "Яндекс ссылки: https://yadi.sk/d/file123, https://disk.yandex.ru/i/folder456"
        
        response = api_client.post('/api/v1/parse', json={'text': text})
        
        if response.status_code != 200:
            self._log_error(response, "Parse Yandex links")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'links' in data
        assert len(data['links']) >= 1
        
        yandex_links = [l for l in data['links'] if l['provider'] == 'yandex']
        assert len(yandex_links) >= 1
        
        print(f"\n✅ Парсинг Яндекс: найдено {len(yandex_links)} ссылок")
    
    def test_parse_google_links(self, api_client):
        """Парсинг ссылок Google Drive через API."""
        text = "Google ссылки: https://drive.google.com/file/d/1abc/view, https://drive.google.com/drive/folders/xyz"
        
        response = api_client.post('/api/v1/parse', json={'text': text})
        
        if response.status_code != 200:
            self._log_error(response, "Parse Google links")
        
        assert response.status_code == 200
        data = response.json()
        
        google_links = [l for l in data['links'] if l['provider'] == 'google']
        assert len(google_links) >= 1
        
        print(f"\n✅ Парсинг Google: найдено {len(google_links)} ссылок")
    
    def test_parse_local_paths(self, api_client):
        """Парсинг локальных путей через API."""
        text = "Локальные пути: /Users/test/docs/file.pdf, C:\\Data\\backup.zip"
        
        response = api_client.post('/api/v1/parse', json={'text': text})
        
        if response.status_code != 200:
            self._log_error(response, "Parse local paths")
        
        assert response.status_code == 200
        data = response.json()
        
        local_links = [l for l in data['links'] if l['provider'] == 'local']
        assert len(local_links) >= 1
        
        print(f"\n✅ Парсинг локальных путей: найдено {len(local_links)} путей")
    
    def test_parse_empty_text(self, api_client):
        """Парсинг пустого текста."""
        response = api_client.post('/api/v1/parse', json={'text': ''})
        
        # Ожидаем ошибку валидации или пустой результат
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert len(data.get('links', [])) == 0
    
    def _log_error(self, response, test_name):
        """Логирование ошибки для передачи AI агенту."""
        error_info = f"""
        ❌ ОШИБКА ТЕСТА: {test_name}
        --------------------------------
        Status Code: {response.status_code}
        Response Body: {response.text}
        Request URL: {response.url}
        --------------------------------
        Пример запроса для воспроизведения:
        curl -X POST {response.url} \\
          -H "Content-Type: application/json" \\
          -d '{{"text": "..."}}'
        """
        print(error_info)


class TestTasksEndpoint:
    """Тесты управления задачами."""
    
    @pytest.mark.dependency(depends=["TestHealthCheck:test_health_endpoint"])
    def test_create_task(self, api_client, test_task_data):
        """Создание новой задачи копирования."""
        response = api_client.post('/api/v1/tasks', json=test_task_data)
        
        if response.status_code != 200:
            self._log_creation_error(response, test_task_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'id' in data
        assert data['name'] == test_task_data['name']
        assert data['status'] == 'pending'
        
        print(f"\n✅ Задача создана: ID={data['id']}, Status={data['status']}")
        
        # Сохраняем ID задачи для последующих тестов
        self.task_id = data['id']
        return data
    
    @pytest.mark.dependency(depends=["test_create_task"])
    def test_get_task(self, api_client, test_task_data):
        """Получение информации о задаче."""
        # Сначала создаём задачу
        create_response = api_client.post('/api/v1/tasks', json=test_task_data)
        task_id = create_response.json()['id']
        
        response = api_client.get(f'/api/v1/tasks/{task_id}')
        
        if response.status_code != 200:
            self._log_error(response, f"Get task {task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['id'] == task_id
        assert data['name'] == test_task_data['name']
        
        print(f"\n✅ Задача получена: ID={data['id']}, Status={data['status']}")
    
    @pytest.mark.dependency(depends=["test_create_task"])
    def test_list_tasks(self, api_client, test_task_data):
        """Получение списка задач."""
        # Создаём тестовую задачу
        api_client.post('/api/v1/tasks', json=test_task_data)
        
        response = api_client.get('/api/v1/tasks')
        
        if response.status_code != 200:
            self._log_error(response, "List tasks")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        print(f"\n✅ Список задач: всего {len(data)} задач")
    
    @pytest.mark.dependency(depends=["test_create_task"])
    def test_update_task_status(self, api_client, test_task_data):
        """Обновление статуса задачи."""
        # Создаём задачу
        create_response = api_client.post('/api/v1/tasks', json=test_task_data)
        task_id = create_response.json()['id']
        
        # Обновляем статус
        update_data = {'status': 'running'}
        response = api_client.patch(f'/api/v1/tasks/{task_id}/status', json=update_data)
        
        if response.status_code != 200:
            self._log_error(response, f"Update task status {task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'running'
        
        print(f"\n✅ Статус обновлён: ID={task_id}, New Status={data['status']}")
    
    @pytest.mark.dependency(depends=["test_create_task"])
    def test_cancel_task(self, api_client, test_task_data):
        """Отмена задачи."""
        # Создаём задачу
        create_response = api_client.post('/api/v1/tasks', json=test_task_data)
        task_id = create_response.json()['id']
        
        # Отменяем задачу
        response = api_client.post(f'/api/v1/tasks/{task_id}/cancel')
        
        if response.status_code != 200:
            self._log_error(response, f"Cancel task {task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'cancelled'
        
        print(f"\n✅ Задача отменена: ID={task_id}")
    
    def _log_creation_error(self, response, task_data):
        """Подробное логирование ошибки создания задачи."""
        error_info = f"""
        ❌ КРИТИЧЕСКАЯ ОШИБКА: Создание задачи
        --------------------------------
        Status Code: {response.status_code}
        Response Body: {response.text}
        Request URL: {response.url}
        
        Данные запроса:
        {task_data}
        --------------------------------
        Пример curl для воспроизведения:
        curl -X POST {response.url} \\
          -H "Content-Type: application/json" \\
          -d '{str(task_data).replace("'", '"")}'
        --------------------------------
        Возможные причины:
        1. База данных недоступна
        2. Ошибка миграций
        3. Некорректная схема данных
        """
        print(error_info)
    
    def _log_error(self, response, test_name):
        """Логирование общей ошибки."""
        error_info = f"""
        ❌ ОШИБКА ТЕСТА: {test_name}
        --------------------------------
        Status Code: {response.status_code}
        Response Body: {response.text[:500]}...
        Request URL: {response.url}
        --------------------------------
        """
        print(error_info)


class TestFullWorkflow:
    """Сквозные тесты полного цикла работы."""
    
    @pytest.mark.dependency(depends=[
        "TestHealthCheck:test_health_endpoint",
        "TestParseEndpoint:test_parse_yandex_links"
    ])
    def test_full_copy_workflow(self, api_client):
        """
        Полный цикл: Парсинг → Создание задачи → Проверка статуса → Отмена.
        """
        print("\n🔄 Запуск полного цикла теста...")
        
        # Шаг 1: Парсинг ссылок
        parse_text = "Файлы: https://yadi.sk/d/testfile123, /Users/test/docs/file.pdf"
        parse_response = api_client.post('/api/v1/parse', json={'text': parse_text})
        
        assert parse_response.status_code == 200
        parse_data = parse_response.json()
        links_count = len(parse_data.get('links', []))
        print(f"   1️⃣  Парсинг: найдено {links_count} ссылок")
        
        # Шаг 2: Создание задачи
        task_data = {
            'name': 'Full Workflow Test',
            'description': 'Автоматический тест полного цикла',
            'source_path': '/tmp/source',
            'destination_path': '/tmp/dest',
            'config': {'test_mode': True}
        }
        
        create_response = api_client.post('/api/v1/tasks', json=task_data)
        assert create_response.status_code == 200
        task = create_response.json()
        task_id = task['id']
        print(f"   2️⃣  Задача создана: {task_id}")
        
        # Шаг 3: Проверка статуса
        status_response = api_client.get(f'/api/v1/tasks/{task_id}')
        assert status_response.status_code == 200
        print(f"   3️⃣  Статус задачи: {task['status']}")
        
        # Шаг 4: Отмена задачи
        cancel_response = api_client.post(f'/api/v1/tasks/{task_id}/cancel')
        assert cancel_response.status_code == 200
        assert cancel_response.json()['status'] == 'cancelled'
        print(f"   4️⃣  Задача отменена")
        
        print("\n✅ Полный цикл успешно завершён!")
