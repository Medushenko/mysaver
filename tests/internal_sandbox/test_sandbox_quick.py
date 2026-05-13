"""
Тесты для внутренней песочницы AI.
Специальные тесты для проверки работы в изолированной среде AI.
Используют абсолютные пути и обходные пути для ограничений песочницы.
"""
import pytest
import sys
import os

# Абсолютный путь к backend в песочнице AI
SANDBOX_BACKEND_PATH = '/workspace/backend'
if SANDBOX_BACKEND_PATH not in sys.path:
    sys.path.insert(0, SANDBOX_BACKEND_PATH)


class TestSandboxEnvironment:
    """Тесты окружения песочницы AI."""
    
    def test_backend_path_exists(self):
        """Проверка доступности backend директории."""
        assert os.path.exists(SANDBOX_BACKEND_PATH), \
            f"Backend директория не найдена: {SANDBOX_BACKEND_PATH}"
        print(f"\n✅ Backend путь доступен: {SANDBOX_BACKEND_PATH}")
    
    def test_app_module_importable(self):
        """Проверка импортируемости модуля app."""
        try:
            import app
            print(f"\n✅ Модуль app импортирован: {app.__file__}")
        except ImportError as e:
            pytest.fail(f"Не удалось импортировать модуль app: {e}")
    
    def test_core_parsers_available(self):
        """Проверка доступности парсеров."""
        from app.core.parsers.yandex import YandexLinkParser
        from app.core.parsers.google import GoogleLinkParser
        from app.core.parsers.local import LocalPathParser
        
        assert YandexLinkParser is not None
        assert GoogleLinkParser is not None
        assert LocalPathParser is not None
        
        print(f"\n✅ Все парсеры доступны")
    
    def test_database_file_exists(self):
        """Проверка существования файла БД SQLite."""
        db_path = os.path.join(SANDBOX_BACKEND_PATH, 'mysaver.db')
        
        # Файл может не существовать, но директория должна быть доступна
        db_dir = os.path.dirname(db_path)
        assert os.path.exists(db_dir), f"Директория БД не найдена: {db_dir}"
        
        if os.path.exists(db_path):
            print(f"\n✅ Файл БД существует: {db_path}")
        else:
            print(f"\n⚠️  Файл БД будет создан при первом запуске: {db_path}")


class TestSandboxParsers:
    """Быстрые тесты парсеров в песочнице."""
    
    def test_yandex_parse_simple(self):
        """Простой тест парсера Яндекс."""
        from app.core.parsers.yandex import YandexLinkParser
        
        parser = YandexLinkParser()
        links = parser.parse("Ссылка: https://yadi.sk/d/test123")
        
        assert len(links) == 1
        assert links[0].provider == "yandex"
        print(f"\n✅ Яндекс парсер: {links[0].url}")
    
    def test_google_parse_simple(self):
        """Простой тест парсера Google."""
        from app.core.parsers.google import GoogleLinkParser
        
        parser = GoogleLinkParser()
        links = parser.parse("Ссылка: https://drive.google.com/file/d/abc123/view")
        
        assert len(links) == 1
        assert links[0].provider == "google"
        print(f"\n✅ Google парсер: {links[0].url}")
    
    def test_local_parse_simple(self):
        """Простой тест парсера локальных путей."""
        from app.core.parsers.local import LocalPathParser
        
        parser = LocalPathParser()
        links = parser.parse("Путь: /Users/test/file.txt")
        
        assert len(links) == 1
        assert links[0].provider == "local"
        print(f"\n✅ Локальный парсер: {links[0].url}")


class TestSandboxQuickCheck:
    """Быстрая проверка ключевых компонентов."""
    
    def test_tree_node_creation(self):
        """Создание узла дерева."""
        from app.core.preview.tree import TreeNode
        
        node = TreeNode(
            id="test_1",
            name="test_file.txt",
            type="file",  # Используем строку вместо enum
            size=1024
        )
        
        assert node.id == "test_1"
        assert node.name == "test_file.txt"
        assert node.type == "file"
        assert node.size == 1024
        
        print(f"\n✅ TreeNode создан: {node.name}")
    
    def test_conflict_policy_enum(self):
        """Проверка enum политик конфликтов."""
        from app.core.conflicts.resolver import ConflictPolicy
        
        policies = [ConflictPolicy.SKIP, ConflictPolicy.OVERWRITE, 
                   ConflictPolicy.KEEP_BOTH, ConflictPolicy.RENAME]
        
        assert len(policies) == 4
        print(f"\n✅ Политики конфликтов: {[p.value for p in policies]}")
    
    def test_import_all_core_modules(self):
        """Проверка импорта всех основных модулей."""
        modules_to_test = [
            'app.core.parsers.base',
            'app.core.parsers.yandex',
            'app.core.parsers.google',
            'app.core.parsers.local',
            'app.core.preview.tree',
            'app.core.conflicts.resolver',
            'app.core.reports.generator',
            'app.core.cache.cleaner',
            'app.models.task',
            'app.schemas.task',
        ]
        
        failed_imports = []
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"  ✓ {module_name}")
            except ImportError as e:
                failed_imports.append((module_name, str(e)))
                print(f"  ✗ {module_name}: {e}")
        
        if failed_imports:
            error_msg = "\n".join([f"{name}: {err}" for name, err in failed_imports])
            pytest.fail(f"Не удалось импортировать модули:\n{error_msg}")
        else:
            print(f"\n✅ Все {len(modules_to_test)} модулей импортированы успешно")
