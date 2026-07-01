"""
Навык помощи в программировании.

Использует CodeLlama через Ollama для:
- Проверки качества кода
- Генерации тестов
- Рефакторинга
- Объяснения кода
- Исправления ошибок
- Оптимизации
- Документирования
- Предложений
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from .base import BaseSkill

logger = logging.getLogger(__name__)


class CodingHelper(BaseSkill):
    """Помощь в программировании."""

    class Language(Enum):
        """Поддерживаемые языки программирования."""
        PYTHON = "python"
        JAVASCRIPT = "javascript"
        JAVA = "java"
        CPP = "c++"
        SQL = "sql"
        RUST = "rust"

    def __init__(self, brain=None, memory=None):
        """Инициализация навыка помощи в программировании."""
        super().__init__(
            name="coding_helper",
            description="Помощь в программировании: проверка, тесты, рефакторинг",
            version="1.0.0",
            priority=70,  # Высокий приоритет
            brain=brain,
            memory=memory,
        )

    def can_handle(self, prompt: str) -> bool:
        """Проверить, может ли обработать запрос."""
        keywords = [
            "код", "программ", "функ", "класс", "bug", "ошибка",
            "тест", "рефактор", "оптимиз", "объясни", "документ",
            "python", "javascript", "java", "sql", "lint",
        ]
        return any(kw in prompt.lower() for kw in keywords)

    def get_capabilities(self) -> List[str]:
        """Получить список возможностей."""
        return [
            "review_code - проверка качества кода",
            "generate_tests - генерация unit тестов",
            "refactor_code - рефакторинг кода",
            "explain_code - объяснение кода",
            "fix_bugs - исправление ошибок",
            "optimize_code - оптимизация производительности",
            "generate_docs - создание документации",
            "suggest_improvements - предложения по улучшению",
        ]

    async def execute(self, prompt: str) -> str:
        """Выполнить команду помощи в программировании."""
        try:
            prompt_lower = prompt.lower()

            if "проверь" in prompt_lower or "review" in prompt_lower:
                return await self._review_code(prompt)

            elif "тест" in prompt_lower or "test" in prompt_lower:
                return await self._generate_tests(prompt)

            elif "рефактор" in prompt_lower or "refactor" in prompt_lower:
                return await self._refactor_code(prompt)

            elif "объясни" in prompt_lower or "explain" in prompt_lower:
                return await self._explain_code(prompt)

            elif "bug" in prompt_lower or "ошибка" in prompt_lower or "error" in prompt_lower:
                return await self._fix_bugs(prompt)

            elif "оптимиз" in prompt_lower or "optimize" in prompt_lower:
                return await self._optimize_code(prompt)

            elif "документ" in prompt_lower or "docs" in prompt_lower:
                return await self._generate_docs(prompt)

            elif "улучш" in prompt_lower or "suggest" in prompt_lower:
                return await self._suggest_improvements(prompt)

            else:
                return "🤖 Команда программирования не распознана"

        except Exception as e:
            self.log_action(
                "execute",
                status="error",
                details={"error": str(e)},
                level="ERROR",
            )
            return f"❌ Ошибка: {e}"

    async def _review_code(self, prompt: str) -> str:
        """Проверить код."""
        if not self.brain:
            return "❌ Мозг не доступен"

        try:
            response = await self.brain.generate(
                prompt=f"""Проверь качество этого кода и дай рекомендации:
{prompt}

Оцени по критериям:
1. Читаемость
2. Производительность
3. Безопасность
4. Следование best practices""",
            )

            self.log_action(
                "review_code",
                status="success",
            )

            return f"""
📝 Проверка кода:

{response}
"""

        except Exception as e:
            return f"❌ Ошибка проверки: {e}"

    async def _generate_tests(self, prompt: str) -> str:
        """Генерировать тесты."""
        if not self.brain:
            return "❌ Мозг не доступен"

        try:
            response = await self.brain.generate(
                prompt=f"""Генерируй unit тесты для этого кода:
{prompt}

Создай тесты с:
1. Проверкой основных случаев
2. Граничными значениями
3. Обработкой ошибок""",
            )

            self.log_action(
                "generate_tests",
                status="success",
            )

            return f"""
🧪 Генерированные тесты:

{response}
"""

        except Exception as e:
            return f"❌ Ошибка генерации тестов: {e}"

    async def _refactor_code(self, prompt: str) -> str:
        """Рефакторинг кода."""
        if not self.brain:
            return "❌ Мозг не доступен"

        try:
            response = await self.brain.generate(
                prompt=f"""Рефакторируй этот код, делая его:
{prompt}

Рекомендации:
1. Упроси логику
2. Устрани дублирование
3. Улучши читаемость""",
            )

            self.log_action(
                "refactor_code",
                status="success",
            )

            return f"""
🔧 Рефакторированный код:

{response}
"""

        except Exception as e:
            return f"❌ Ошибка рефакторинга: {e}"

    async def _explain_code(self, prompt: str) -> str:
        """Объяснить код."""
        if not self.brain:
            return "❌ Мозг не доступен"

        try:
            response = await self.brain.generate(
                prompt=f"""Объясни этот код просто и понятно:
{prompt}

Объяснение должно включать:
1. Что делает код
2. Как работает логика
3. Почему используются эти подходы""",
            )

            self.log_action(
                "explain_code",
                status="success",
            )

            return f"""
📖 Объяснение кода:

{response}
"""

        except Exception as e:
            return f"❌ Ошибка объяснения: {e}"

    async def _fix_bugs(self, prompt: str) -> str:
        """Исправить ошибки."""
        if not self.brain:
            return "❌ Мозг не доступен"

        try:
            response = await self.brain.generate(
                prompt=f"""Найди и исправь ошибки в коде:
{prompt}

Для каждой ошибки:
1. Объясни что не так
2. Покажи исправленный код
3. Объясни почему это работает""",
            )

            self.log_action(
                "fix_bugs",
                status="success",
            )

            return f"""
🐛 Исправленный код:

{response}
"""

        except Exception as e:
            return f"❌ Ошибка исправления: {e}"

    async def _optimize_code(self, prompt: str) -> str:
        """Оптимизировать код."""
        if self.sandbox_mode:
            self.log_action(
                "optimize_code",
                status="simulated",
            )
            return "🔒 [SIMULATED] Код оптимизирован: снижение памяти на 30%"

        return "ℹ️ Оптимизация кода требует анализа производительности"

    async def _generate_docs(self, prompt: str) -> str:
        """Генерировать документацию."""
        if not self.brain:
            return "❌ Мозг не доступен"

        try:
            response = await self.brain.generate(
                prompt=f"""Создай документацию для этого кода:
{prompt}

Документация должна включать:
1. Описание функций/классов
2. Параметры и возвращаемые значения
3. Примеры использования
4. Возможные ошибки""",
            )

            self.log_action(
                "generate_docs",
                status="success",
            )

            return f"""
📚 Документация:

{response}
"""

        except Exception as e:
            return f"❌ Ошибка генерации документации: {e}"

    async def _suggest_improvements(self, prompt: str) -> str:
        """Предложить улучшения."""
        if not self.brain:
            return "❌ Мозг не доступен"

        try:
            response = await self.brain.generate(
                prompt=f"""Предложи улучшения для этого кода:
{prompt}

Рекомендации:
1. Производительность
2. Безопасность
3. Масштабируемость
4. Поддерживаемость
5. Best practices""",
            )

            self.log_action(
                "suggest_improvements",
                status="success",
            )

            return f"""
💡 Предложения по улучшению:

{response}
"""

        except Exception as e:
            return f"❌ Ошибка предложения: {e}"

    def __repr__(self) -> str:
        """Строковое представление."""
        return "CodingHelper()"
