"""
Маршрутизатор запросов для выбора оптимальной обработки.

Выбирает уровень обработки в зависимости от сложности запроса.
"""

import logging
from typing import Optional, Tuple
from enum import Enum
import re

logger = logging.getLogger(__name__)


class ProcessingLevel(Enum):
    """Уровни обработки запросов."""

    COMMAND = 1  # Точные команды (мгновенно)
    PATTERN = 2  # Fuzzy matching с паттернами
    LIGHT = 3  # Phi-3 для простых запросов
    GENERAL = 4  # Llama 3 для обычных запросов
    COMPLEX = 5  # Llama 3 для сложных рассуждений
    CODE = 6  # CodeLlama для кода


class QueryRouter:
    """
    Маршрутизатор запросов.

    Анализирует запрос и выбирает оптимальный уровень обработки.
    """

    # Точные команды
    EXACT_COMMANDS = {
        "/help": "Справка",
        "/stats": "Статистика",
        "/clear": "Очистка памяти",
        "/exit": "Выход",
        "/skills": "Список навыков",
        "/export": "Экспорт",
    }

    # Паттерны для fuzzy matching
    PATTERNS = {
        r"(привет|здравствуй|привет|привет|какда|как ты)": "greeting",
        r"(спасибо|благодарю|спасибо|спс)": "thanks",
        r"(пока|до свидания|до встречи|выход)": "goodbye",
        r"(что это|что это такое|расскажи)": "explain",
        r"(помощь|помоги|справка)": "help",
    }

    # Индикаторы сложности
    CODE_INDICATORS = [
        "код", "функ", "класс", "def", "class", "import",
        "python", "javascript", "java", "sql", "bug", "error",
    ]

    COMPLEX_INDICATORS = [
        "почему", "как", "объясни", "анализ", "рассуждение",
        "что если", "сравни", "помоги решить", "как работает",
    ]

    SIMPLE_INDICATORS = [
        "что", "когда", "где", "кто", "какой",
        "скажи", "расскажи", "примеры",
    ]

    def __init__(self):
        """Инициализация маршрутизатора."""
        logger.info("🚦 Инициализация QueryRouter")

    def route(self, query: str) -> Tuple[ProcessingLevel, float]:
        """
        Маршрутизировать запрос и вернуть уровень обработки.

        Args:
            query: Текст запроса

        Returns:
            Кортеж (уровень обработки, уверенность 0-1)
        """
        query_lower = query.lower().strip()

        # Level 1: Точные команды
        if query_lower in self.EXACT_COMMANDS:
            logger.debug(f"🎯 Level 1 (COMMAND): {query_lower}")
            return ProcessingLevel.COMMAND, 0.99

        # Level 2: Fuzzy matching
        for pattern, category in self.PATTERNS.items():
            if re.search(pattern, query_lower):
                logger.debug(f"🎯 Level 2 (PATTERN): {category}")
                return ProcessingLevel.PATTERN, 0.85

        # Определяем сложность
        complexity_score = self._calculate_complexity(query)

        # Level 5: Код
        if self._is_code_query(query_lower):
            logger.debug(f"🎯 Level 6 (CODE)")
            return ProcessingLevel.CODE, 0.9

        # Level 4: Сложные запросы
        if complexity_score > 0.7 or self._is_complex_query(query_lower):
            logger.debug(f"🎯 Level 5 (COMPLEX): complexity={complexity_score:.2f}")
            return ProcessingLevel.COMPLEX, complexity_score

        # Level 3: Простые запросы
        if complexity_score < 0.3 or self._is_simple_query(query_lower):
            logger.debug(f"🎯 Level 3 (LIGHT): complexity={complexity_score:.2f}")
            return ProcessingLevel.LIGHT, 0.7

        # Level 4: Обычные запросы (по умолчанию)
        logger.debug(f"🎯 Level 4 (GENERAL): complexity={complexity_score:.2f}")
        return ProcessingLevel.GENERAL, 0.6

    def _calculate_complexity(self, query: str) -> float:
        """
        Рассчитать сложность запроса (0-1).

        Args:
            query: Текст запроса

        Returns:
            Оценка сложности (0-1)
        """
        query_lower = query.lower()
        score = 0.0

        # Длина запроса
        word_count = len(query.split())
        if word_count > 20:
            score += 0.2
        elif word_count > 10:
            score += 0.1

        # Сложные слова
        complex_words = [
            "анализ", "рассуждение", "объясни", "почему", "как",
            "сравни", "отношение", "проблема", "решение",
        ]
        complex_count = sum(1 for word in complex_words if word in query_lower)
        score += min(0.3, complex_count * 0.1)

        # Наличие условных конструкций
        if any(cond in query_lower for cond in ["если", "когда", "то", "иначе"]):
            score += 0.2

        # Запросы на объяснение
        if any(exp in query_lower for exp in ["объясни", "как это работает", "почему"]):
            score += 0.25

        return min(1.0, score)

    def _is_code_query(self, query: str) -> bool:
        """Проверить, это ли запрос о коде."""
        code_count = sum(
            1 for indicator in self.CODE_INDICATORS
            if indicator in query
        )
        return code_count >= 2

    def _is_complex_query(self, query: str) -> bool:
        """Проверить, это ли сложный запрос."""
        complex_count = sum(
            1 for indicator in self.COMPLEX_INDICATORS
            if indicator in query
        )
        return complex_count >= 1

    def _is_simple_query(self, query: str) -> bool:
        """Проверить, это ли простой запрос."""
        if len(query) < 20:
            return True

        simple_count = sum(
            1 for indicator in self.SIMPLE_INDICATORS
            if indicator in query
        )
        return simple_count >= 2

    def get_model_for_level(self, level: ProcessingLevel) -> str:
        """
        Получить рекомендуемую модель для уровня.

        Args:
            level: Уровень обработки

        Returns:
            Имя модели
        """
        model_map = {
            ProcessingLevel.COMMAND: "command",
            ProcessingLevel.PATTERN: "pattern",
            ProcessingLevel.LIGHT: "phi3:mini",
            ProcessingLevel.GENERAL: "llama3:8b",
            ProcessingLevel.COMPLEX: "llama3:8b",
            ProcessingLevel.CODE: "codellama:13b",
        }
        return model_map.get(level, "llama3:8b")

    def __repr__(self) -> str:
        """Строковое представление."""
        return "QueryRouter()"