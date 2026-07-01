"""
Интеграция с менеджером задач (Todoist / локальный).
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .import BaseIntegration, IntegrationError, cached

logger = logging.getLogger(__name__)


class TodoIntegration(BaseIntegration):
    """Интеграция с менеджером задач."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Инициализация."""
        super().__init__("todo", config)
        self.tasks: List[Dict[str, Any]] = []

    async def _init(self) -> None:
        """Инициализировать todo."""
        logger.info("✓ Инициализирую менеджер задач (мок)")

    @cached(ttl=300)
    async def get_tasks(
        self,
        filter_: str = "today",
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Получить задачи.

        Args:
            filter_: Фильтр (today, week, all)
            limit: Лимит задач

        Returns:
            Список задач
        """
        if not self._initialized:
            raise IntegrationError("Todo не инициализирован")

        try:
            async with self.rate_limiter:
                # Мок задачи
                tasks = [
                    {
                        "id": "1",
                        "title": "Завершить отчет",
                        "priority": "high",
                        "due_date": "2024-01-16",
                        "completed": False,
                    },
                    {
                        "id": "2",
                        "title": "Ревью кода",
                        "priority": "medium",
                        "due_date": "2024-01-17",
                        "completed": False,
                    },
                    {
                        "id": "3",
                        "title": "Встреча с клиентом",
                        "priority": "high",
                        "due_date": "2024-01-16",
                        "completed": False,
                    },
                ]

                logger.info(f"✅ Получено {len(tasks)} задач")
                return tasks[:limit]

        except Exception as e:
            logger.error(f"❌ Ошибка получения задач: {e}")
            raise

    async def create_task(
        self,
        title: str,
        priority: str = "medium",
        due_date: Optional[datetime] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Создать задачу.

        Args:
            title: Название
            priority: Приоритет (low, medium, high)
            due_date: Дедлайн
            description: Описание

        Returns:
            Созданная задача
        """
        if not self._initialized:
            raise IntegrationError("Todo не инициализирован")

        try:
            async with self.rate_limiter:
                task = {
                    "id": "new",
                    "title": title,
                    "priority": priority,
                    "due_date": due_date.isoformat() if due_date else None,
                    "description": description,
                    "completed": False,
                }

                logger.info(f"✅ Задача создана: {title}")
                return task

        except Exception as e:
            logger.error(f"❌ Ошибка создания задачи: {e}")
            raise

    async def prioritize_tasks(self, brain=None) -> List[Dict[str, Any]]:
        """
        Приоритизировать задачи через LLM.

        Args:
            brain: Объект мозга

        Returns:
            Отсортированные задачи
        """
        try:
            tasks = await self.get_tasks()

            if brain:
                # Используем LLM для приоритизации
                task_list = "\n".join([f"- {t['title']}" for t in tasks])
                prompt = f"Приоритизируй эти задачи по важности:\n{task_list}"

                # Сортируем по текущему приоритету
                tasks.sort(
                    key=lambda t: {"high": 1, "medium": 2, "low": 3}.get(t.get("priority", "medium"), 2)
                )

            logger.info(f"✅ Задачи приоритизированы")
            return tasks

        except Exception as e:
            logger.error(f"❌ Ошибка приоритизации: {e}")
            return []

    async def complete_task(self, task_id: str) -> bool:
        """Отметить задачу как выполненную."""
        try:
            logger.info(f"✅ Задача отмечена как выполненная: {task_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка завершения задачи: {e}")
            return False