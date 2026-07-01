"""
Система самодиагностики и мониторинга здоровья ассистента.

Проверяет доступность компонентов и отправляет метрики.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram
except ImportError:
    Counter = Gauge = Histogram = None


class HealthCheck:
    """Система проверки здоровья ассистента."""

    def __init__(self):
        """Инициализация health check."""
        self.start_time = datetime.now()
        self.component_status: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}

        # Prometheus метрики (если доступны)
        if Counter and Gauge:
            self.request_counter = Counter(
                "assistant_requests_total",
                "Total requests",
            )
            self.error_counter = Counter(
                "assistant_errors_total",
                "Total errors",
            )
            self.response_time = Histogram(
                "assistant_response_seconds",
                "Response time",
            )
            self.active_requests = Gauge(
                "assistant_active_requests",
                "Active requests",
            )
        else:
            self.request_counter = None
            self.error_counter = None
            self.response_time = None
            self.active_requests = None

        logger.info("✅ Система HealthCheck инициализирована")

    def check_component(
        self,
        name: str,
        check_func,
        timeout: float = 5.0,
    ) -> Dict[str, Any]:
        """
        Проверить компонент.

        Args:
            name: Имя компонента
            check_func: Функция проверки
            timeout: Таймаут проверки

        Returns:
            Результат проверки
        """
        try:
            start = time.time()
            result = check_func()
            elapsed = time.time() - start

            status = {
                "name": name,
                "status": "healthy" if result else "degraded",
                "response_time": elapsed,
                "last_checked": datetime.now().isoformat(),
            }

            self.component_status[name] = status
            logger.info(f"✅ {name}: {status['status']}")
            return status

        except Exception as e:
            status = {
                "name": name,
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat(),
            }

            self.component_status[name] = status
            logger.error(f"❌ {name}: {e}")
            return status

    def record_request(self, duration: float, success: bool = True) -> None:
        """
        Записать метрику запроса.

        Args:
            duration: Длительность запроса
            success: Успешен ли запрос
        """
        if self.request_counter:
            self.request_counter.inc()

        if not success and self.error_counter:
            self.error_counter.inc()

        if self.response_time:
            self.response_time.observe(duration)

    def get_status(self) -> Dict[str, Any]:
        """Получить статус ассистента."""
        uptime = (datetime.now() - self.start_time).total_seconds()

        # Определяем общий статус
        statuses = [
            c.get("status") for c in self.component_status.values()
        ]
        overall_status = "healthy"
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "uptime_seconds": uptime,
            "components": self.component_status,
            "timestamp": datetime.now().isoformat(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Получить метрики в формате Prometheus."""
        return {
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "components": self.component_status,
            "timestamp": datetime.now().isoformat(),
        }

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"HealthCheck("
            f"components={len(self.component_status)}, "
            f"status={self.get_status().get('status')})"
        )