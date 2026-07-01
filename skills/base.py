"""
Базовый класс для всех навыков ассистента.

Предоставляет общие методы для логирования, валидации, безопасности.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from datetime import datetime

from config import config

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """
    Базовый класс для всех навыков.

    Attributes:
        name: Имя навыка
        description: Описание навыка
        version: Версия навыка
        priority: Приоритет (0-100, выше = приоритетнее)
        sandbox_mode: Режим песочницы
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        priority: int = 50,
        brain=None,
        memory=None,
    ):
        """
        Инициализация навыка.

        Args:
            name: Имя навыка
            description: Описание навыка
            version: Версия
            priority: Приоритет (0-100)
            brain: Ссылка на мозг ассистента
            memory: Ссылка на систему памяти
        """
        self.name = name
        self.description = description
        self.version = version
        self.priority = max(0, min(100, priority))
        self.is_enabled = True
        self.sandbox_mode = config.mode.sandbox_mode
        self.brain = brain
        self.memory = memory
        self.action_log: List[Dict[str, Any]] = []

        logger.info(f"🎯 Инициализирован навык: {name} v{version}")

    @abstractmethod
    def can_handle(self, prompt: str) -> bool:
        """
        Определить, может ли этот навык обработать запрос.

        Args:
            prompt: Текст запроса

        Returns:
            True если навык может обработать запрос
        """
        pass

    @abstractmethod
    async def execute(self, prompt: str) -> str:
        """
        Выполнить действие навыка.

        Args:
            prompt: Текст запроса

        Returns:
            Результат выполнения
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Получить список возможностей навыка.

        Returns:
            Список строк с описанием возможностей
        """
        pass

    def log_action(
        self,
        action: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        level: str = "INFO",
    ) -> None:
        """
        Логировать действие навыка.

        Args:
            action: Название действия
            status: Статус (success, error, warning, simulated)
            details: Дополнительные детали
            level: Уровень логирования
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "skill": self.name,
            "action": action,
            "status": status,
            "sandbox": self.sandbox_mode,
            "details": details or {},
        }

        self.action_log.append(log_entry)

        # Форматируем сообщение
        status_emoji = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "simulated": "🔒",
        }.get(status, "ℹ️")

        message = (
            f"{status_emoji} [{self.name}] {action}"
        )

        if self.sandbox_mode and status != "simulated":
            message += " [SIMULATED]"

        # Логируем
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

    def safe_execute(self, func: Callable) -> Callable:
        """
        Декоратор для безопасного выполнения функций.

        Args:
            func: Функция для выполнения

        Returns:
            Обёрнутая функция
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                self.log_action(
                    f"Начало: {func.__name__}",
                    status="info",
                )
                result = await func(*args, **kwargs)
                self.log_action(
                    f"Завершено: {func.__name__}",
                    status="success",
                )
                return result
            except Exception as e:
                self.log_action(
                    f"Ошибка в {func.__name__}",
                    status="error",
                    details={"error": str(e)},
                    level="ERROR",
                )
                raise

        return wrapper

    async def require_confirmation(
        self,
        action: str,
        critical: bool = False,
    ) -> bool:
        """
        Требовать подтверждение для опасной операции.

        Args:
            action: Описание действия
            critical: Критичная ли операция

        Returns:
            True если подтверждено
        """
        if self.sandbox_mode:
            self.log_action(
                f"Требуемое подтверждение (в sandbox): {action}",
                status="simulated",
            )
            return True  # В sandbox автоматически подтверждаем

        level = "CRITICAL" if critical else "WARNING"
        self.log_action(
            f"Требуется подтверждение: {action}",
            status="warning",
            level=level,
        )

        # В реальности нужна интеграция с UI
        return True

    def validate_params(
        self,
        params: Dict[str, Any],
        required: List[str],
        types: Optional[Dict[str, type]] = None,
    ) -> bool:
        """
        Валидировать параметры.

        Args:
            params: Параметры
            required: Требуемые параметры
            types: Ожидаемые типы

        Returns:
            True если параметры валидны

        Raises:
            ValueError: Если параметры невалидны
        """
        # Проверяем обязательные параметры
        for req_param in required:
            if req_param not in params:
                raise ValueError(f"Отсутствует требуемый параметр: {req_param}")

        # Проверяем типы
        if types:
            for param_name, expected_type in types.items():
                if param_name in params:
                    if not isinstance(params[param_name], expected_type):
                        raise ValueError(
                            f"Параметр {param_name} должен быть {expected_type}, "
                            f"получен {type(params[param_name])}"
                        )

        return True

    def get_info(self) -> Dict[str, Any]:
        """
        Получить информацию о навыке.

        Returns:
            Словарь с информацией
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "priority": self.priority,
            "enabled": self.is_enabled,
            "sandbox_mode": self.sandbox_mode,
            "capabilities": self.get_capabilities(),
            "actions_count": len(self.action_log),
        }

    def get_action_log(self) -> List[Dict[str, Any]]:
        """
        Получить логи действий.

        Returns:
            Список логов
        """
        return self.action_log.copy()

    def clear_action_log(self) -> None:
        """Очистить логи действий."""
        self.action_log.clear()

    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"enabled={self.is_enabled}, "
            f"priority={self.priority})"
        )