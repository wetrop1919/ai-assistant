"""
Тесты для навыков ассистента.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Импортируем после добавления пути
from skills.base import BaseSkill
from skills.system import SystemControl
from skills.files import FileManager
from skills.web import WebTools
from skills.automation import Automation
from skills.coding import CodingHelper
from skills.registry import SkillRegistry


class TestBaseSkill:
    """Тесты базового класса навыка."""

    def test_skill_initialization(self):
        """Тест инициализации навыка."""

        class TestSkill(BaseSkill):
            def can_handle(self, prompt: str) -> bool:
                return "test" in prompt

            async def execute(self, prompt: str) -> str:
                return "test response"

            def get_capabilities(self):
                return ["test_capability"]

        skill = TestSkill("test_skill", "A test skill")
        assert skill.name == "test_skill"
        assert skill.is_enabled == True
        assert skill.priority == 50

    def test_skill_can_handle(self):
        """Тест проверки обработки запроса."""

        class TestSkill(BaseSkill):
            def can_handle(self, prompt: str) -> bool:
                return "test" in prompt.lower()

            async def execute(self, prompt: str) -> str:
                return "response"

            def get_capabilities(self):
                return []

        skill = TestSkill("test", "Test")
        assert skill.can_handle("this is a test")
        assert not skill.can_handle("this is not")

    def test_skill_log_action(self):
        """Тест логирования действия."""

        class TestSkill(BaseSkill):
            def can_handle(self, prompt: str) -> bool:
                return True

            async def execute(self, prompt: str) -> str:
                return "response"

            def get_capabilities(self):
                return []

        skill = TestSkill("test", "Test")
        skill.log_action("test_action", status="success", details={"key": "value"})

        assert len(skill.action_log) == 1
        assert skill.action_log[0]["action"] == "test_action"
        assert skill.action_log[0]["status"] == "success"

    def test_skill_validate_params(self):
        """Тест валидации параметров."""

        class TestSkill(BaseSkill):
            def can_handle(self, prompt: str) -> bool:
                return True

            async def execute(self, prompt: str) -> str:
                return "response"

            def get_capabilities(self):
                return []

        skill = TestSkill("test", "Test")

        # Должен пройти валидацию
        assert skill.validate_params(
            {"name": "test", "value": 42},
            required=["name"],
            types={"value": int},
        )

        # Должна вызвать ошибку - отсутствует требуемый параметр
        with pytest.raises(ValueError):
            skill.validate_params(
                {"value": 42},
                required=["name"],
            )

        # Должна вызвать ошибку - неверный тип
        with pytest.raises(ValueError):
            skill.validate_params(
                {"value": "not_int"},
                types={"value": int},
            )


class TestSystemControl:
    """Тесты навыка управления системой."""

    def test_system_control_initialization(self):
        """Тест инициализации."""
        skill = SystemControl()
        assert skill.name == "system_control"
        capabilities = skill.get_capabilities()
        assert len(capabilities) > 0

    def test_can_handle_system_commands(self):
        """Тест распознавания системных команд."""
        skill = SystemControl()
        assert skill.can_handle("какая система работает")
        assert skill.can_handle("информация о процессах")
        assert skill.can_handle("память и диск")

    @pytest.mark.asyncio
    async def test_system_info_command(self):
        """Тест команды информации о системе."""
        skill = SystemControl()
        result = await skill.execute("информация о системе")
        assert result is not None
        assert isinstance(result, str)


class TestFileManager:
    """Тесты навыка управления файлами."""

    def test_file_manager_initialization(self):
        """Тест инициализации."""
        skill = FileManager()
        assert skill.name == "file_manager"
        capabilities = skill.get_capabilities()
        assert "smart_search" in str(capabilities).lower()

    def test_can_handle_file_commands(self):
        """Тест распознавания команд файлов."""
        skill = FileManager()
        assert skill.can_handle("найди файл")
        assert skill.can_handle("поиск в папке")
        assert skill.can_handle("дубликаты файлов")

    @pytest.mark.asyncio
    async def test_file_search_command(self):
        """Тест команды поиска файлов."""
        skill = FileManager()
        result = await skill.execute("найди файлы")
        assert result is not None
        assert isinstance(result, str)


class TestWebTools:
    """Тесты навыка веб-инструментов."""

    def test_web_tools_initialization(self):
        """Тест инициализации."""
        skill = WebTools()
        assert skill.name == "web_tools"
        capabilities = skill.get_capabilities()
        assert len(capabilities) > 0

    def test_can_handle_web_commands(self):
        """Тест распознавания веб-команд."""
        skill = WebTools()
        assert skill.can_handle("поиск в интернете")
        assert skill.can_handle("погода в Москве")
        assert skill.can_handle("новости")


class TestAutomation:
    """Тесты навыка автоматизации."""

    def test_automation_initialization(self):
        """Тест инициализации."""
        skill = Automation()
        assert skill.name == "automation"
        capabilities = skill.get_capabilities()
        assert "record_macro" in str(capabilities).lower()

    def test_can_handle_automation_commands(self):
        """Тест распознавания команд автоматизации."""
        skill = Automation()
        assert skill.can_handle("запиши макрос")
        assert skill.can_handle("автоматизация")
        assert skill.can_handle("триггер папки")

    @pytest.mark.asyncio
    async def test_macro_recording(self):
        """Тест записи макроса."""
        skill = Automation()
        result = await skill.execute("запиши макрос test")
        assert "тест" in result.lower() or "macro" in result.lower()


class TestCodingHelper:
    """Тесты навыка помощи в программировании."""

    def test_coding_helper_initialization(self):
        """Тест инициализации."""
        skill = CodingHelper()
        assert skill.name == "coding_helper"
        capabilities = skill.get_capabilities()
        assert "review_code" in str(capabilities).lower()

    def test_can_handle_coding_commands(self):
        """Тест распознавания команд программирования."""
        skill = CodingHelper()
        assert skill.can_handle("проверь код")
        assert skill.can_handle("генерируй тесты")
        assert skill.can_handle("рефакторинг")


class TestSkillRegistry:
    """Тесты реестра навыков."""

    def test_registry_initialization(self):
        """Тест инициализации реестра."""
        registry = SkillRegistry()
        assert len(registry.skills) > 0

    def test_register_skill(self):
        """Тест регистрации навыка."""

        class TestSkill(BaseSkill):
            def can_handle(self, prompt: str) -> bool:
                return True

            async def execute(self, prompt: str) -> str:
                return "test"

            def get_capabilities(self):
                return []

        registry = SkillRegistry()
        initial_count = len(registry.skills)
        registry.register(TestSkill("custom_skill", "A custom skill"))
        assert len(registry.skills) == initial_count + 1

    def test_find_skill(self):
        """Тест поиска навыка."""
        registry = SkillRegistry()
        skill = registry.find_skill("система")
        assert skill is not None
        assert hasattr(skill, "can_handle")

    def test_skill_priority_sorting(self):
        """Тест сортировки по приоритету."""
        registry = SkillRegistry()
        priorities = [skill.priority for skill in registry.skills]
        assert priorities == sorted(priorities, reverse=True)

    @pytest.mark.asyncio
    async def test_execute_skill(self):
        """Тест выполнения навыка."""
        registry = SkillRegistry()
        result = await registry.execute_skill("система")
        # Результат может быть None или строка
        assert result is None or isinstance(result, str)

    def test_enable_disable_skill(self):
        """Тест включения/отключения навыка."""
        registry = SkillRegistry()
        skill_name = registry.skills[0].name

        # Отключаем
        assert registry.disable_skill(skill_name)
        assert not registry.get_skill_by_name(skill_name).is_enabled

        # Включаем
        assert registry.enable_skill(skill_name)
        assert registry.get_skill_by_name(skill_name).is_enabled

    def test_get_all_skills(self):
        """Тест получения всех навыков."""
        registry = SkillRegistry()
        skills_info = registry.get_all_skills()
        assert isinstance(skills_info, list)
        assert all("name" in skill for skill in skills_info)
        assert all("enabled" in skill for skill in skills_info)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])