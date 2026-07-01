"""
Система подтверждения опасных действий.
"""

import logging
import asyncio
from typing import Optional, Callable
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class ConfirmationRequest:
    """Запрос подтверждения."""

    def __init__(
        self,
        action: str,
        risk_level: str,
        timeout: int = 30,
        auto_confirm: bool = False,
    ):
        """
        Инициализация.

        Args:
            action: Действие
            risk_level: Уровень риска
            timeout: Таймаут в секундах
            auto_confirm: Автоматически подтвердить
        """
        self.id = str(uuid.uuid4())
        self.action = action
        self.risk_level = risk_level
        self.timeout = timeout
        self.auto_confirm = auto_confirm
        self.created_at = datetime.now()
        self.confirmed = None
        self.reason = ""

    def is_expired(self) -> bool:
        """Проверить истечение."""
        return (datetime.now() - self.created_at).total_seconds() > self.timeout

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"ConfirmationRequest(id={self.id}, action={self.action})"


class ConfirmationManager:
    """Менеджер подтверждений."""

    def __init__(self):
        """Инициализация."""
        self.pending_requests: dict = {}
        self.confirmed_actions: dict = {}
        logger.info("✅ ConfirmationManager инициализирован")

    async def request_confirmation(
        self,
        action: str,
        risk_level: str,
        timeout: int = 30,
        callback: Optional[Callable] = None,
    ) -> bool:
        """
        Запросить подтверждение.

        Args:
            action: Действие
            risk_level: Уровень риска
            timeout: Таймаут
            callback: Функция обратного вызова при подтверждении

        Returns:
            True если подтверждено
        """
        request = ConfirmationRequest(action, risk_level, timeout)
        self.pending_requests[request.id] = request

        logger.warning(
            f"⚠️ Требуется подтверждение для {action} ({risk_level}) "
            f"Автоотмена через {timeout}с"
        )

        # Ждем подтверждения или истечения таймаута
        start = datetime.now()
        while (datetime.now() - start).total_seconds() < timeout:
            if request.confirmed is not None:
                if request.confirmed:
                    logger.info(f"✅ Действие подтверждено: {action}")
                    if callback:
                        await callback() if asyncio.iscoroutinefunction(callback) else callback()
                    return True
                else:
                    logger.info(f"🚫 Действие отклонено: {action}")
                    return False

            await asyncio.sleep(0.1)

        # Таймаут
        logger.warning(f"⏱️ Время подтверждения истекло: {action}")
        del self.pending_requests[request.id]
        return False

    def confirm(self, request_id: str) -> bool:
        """
        Подтвердить запрос.

        Args:
            request_id: ID запроса

        Returns:
            True если успешно
        """
        if request_id in self.pending_requests:
            self.pending_requests[request_id].confirmed = True
            self.confirmed_actions[request_id] = True
            return True
        return False

    def deny(self, request_id: str, reason: str = "") -> bool:
        """
        Отклонить запрос.

        Args:
            request_id: ID запроса
            reason: Причина

        Returns:
            True если успешно
        """
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            request.confirmed = False
            request.reason = reason
            return True
        return False

    def get_pending_requests(self) -> dict:
        """Получить ожидающие запросы."""
        return {
            rid: req for rid, req in self.pending_requests.items()
            if not req.is_expired()
        }

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"ConfirmationManager("
            f"pending={len(self.pending_requests)}, "
            f"confirmed={len(self.confirmed_actions)})"
        )