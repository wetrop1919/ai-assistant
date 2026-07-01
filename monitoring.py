"""
Система мониторинга и сбора метрик.
"""

import logging
from typing import Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Сбор метрик производительности."""

    def __init__(self):
        """Инициализация сборщика метрик."""
        self.metrics: Dict[str, Any] = {
            "start_time": datetime.now().isoformat(),
            "requests": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "average_time": 0.0,
            },
            "models": {},
            "memory": {},
            "errors": [],
        }

    def record_request(
        self,
        model: str,
        duration: float,
        success: bool = True,
        tokens: int = 0,
    ) -> None:
        """Записать метрику запроса."""
        self.metrics["requests"]["total"] += 1

        if success:
            self.metrics["requests"]["successful"] += 1
        else:
            self.metrics["requests"]["failed"] += 1

        # Обновляем время ответа
        avg = self.metrics["requests"]["average_time"]
        total = self.metrics["requests"]["total"]
        self.metrics["requests"]["average_time"] = (
            (avg * (total - 1) + duration) / total
        )

        # Записываем метрики модели
        if model not in self.metrics["models"]:
            self.metrics["models"][model] = {
                "requests": 0,
                "total_time": 0.0,
                "average_time": 0.0,
                "tokens_generated": 0,
            }

        model_metrics = self.metrics["models"][model]
        model_metrics["requests"] += 1
        model_metrics["total_time"] += duration
        model_metrics["average_time"] = (
            model_metrics["total_time"] / model_metrics["requests"]
        )
        model_metrics["tokens_generated"] += tokens

    def record_error(self, error: str, context: str = "") -> None:
        """Записать ошибку."""
        self.metrics["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "context": context,
        })

    def get_metrics(self) -> Dict[str, Any]:
        """Получить метрики."""
        return self.metrics

    def get_prometheus_format(self) -> str:
        """Получить метрики в формате Prometheus."""
        lines = []

        # Request metrics
        lines.append(f"# HELP assistant_requests_total Total requests")
        lines.append(f"# TYPE assistant_requests_total counter")
        lines.append(
            f"assistant_requests_total {self.metrics['requests']['total']}"
        )

        lines.append(f"# HELP assistant_requests_failed Failed requests")
        lines.append(f"# TYPE assistant_requests_failed counter")
        lines.append(
            f"assistant_requests_failed {self.metrics['requests']['failed']}"
        )

        lines.append(f"# HELP assistant_response_time_seconds Average response time")
        lines.append(f"# TYPE assistant_response_time_seconds gauge")
        lines.append(
            f"assistant_response_time_seconds {self.metrics['requests']['average_time']}"
        )

        # Model metrics
        for model, metrics in self.metrics["models"].items():
            lines.append(
                f"# HELP assistant_model_requests Total requests for model"
            )
            lines.append(f"# TYPE assistant_model_requests counter")
            lines.append(
                f'assistant_model_requests{{model="{model}"}} {metrics["requests"]}'
            )

        return "\n".join(lines)

    def export_json(self, filepath: str) -> None:
        """Экспортировать метрики в JSON."""
        try:
            with open(filepath, "w") as f:
                json.dump(self.metrics, f, indent=2)
            logger.info(f"✅ Метрики экспортированы в {filepath}")
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта метрик: {e}")

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"MetricsCollector("
            f"total_requests={self.metrics['requests']['total']}, "
            f"avg_time={self.metrics['requests']['average_time']:.2f}s)"
        )