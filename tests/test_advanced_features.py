"""
Тесты расширенных функций ассистента.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Импортируем после добавления пути
from core.router import QueryRouter, ProcessingLevel
from core.self_check import HealthCheck


class TestQueryRouter:
    """Тесты маршрутизатора запросов."""

    def test_router_initialization(self):
        """Тест инициализации маршрутизатора."""
        router = QueryRouter()
        assert router is not None

    def test_route_exact_command(self):
        """Тест маршрутизации точной команды."""
        router = QueryRouter()
        level, confidence = router.route("/help")
        assert level == ProcessingLevel.COMMAND
        assert confidence > 0.9

    def test_route_greeting(self):
        """Тест маршрутизации приветствия."""
        router = QueryRouter()
        level, confidence = router.route("привет")
        assert level == ProcessingLevel.PATTERN
        assert confidence > 0.8

    def test_route_complex_query(self):
        """Тест маршрутизации сложного запроса."""
        router = QueryRouter()
        level, confidence = router.route(
            "Объясни, почему искусственный интеллект работает эффективнее"
        )
        assert level in [ProcessingLevel.COMPLEX, ProcessingLevel.GENERAL]

    def test_route_code_query(self):
        """Тест маршрутизации запроса о коде."""
        router = QueryRouter()
        level, confidence = router.route("Напиши Python функцию для сортировки")
        assert level == ProcessingLevel.CODE

    def test_complexity_calculation(self):
        """Тест расчета сложности запроса."""
        router = QueryRouter()
        complexity = router._calculate_complexity("простой запрос")
        assert 0 <= complexity <= 1

    def test_get_model_for_level(self):
        """Тест получения модели для уровня."""
        router = QueryRouter()
        model = router.get_model_for_level(ProcessingLevel.CODE)
        assert "codellama" in model or model == "command"

    def test_simple_query_detection(self):
        """Тест обнаружения простых запросов."""
        router = QueryRouter()
        level, conf = router.route("Что такое Python?")
        assert level in [ProcessingLevel.LIGHT, ProcessingLevel.GENERAL]

    def test_pattern_matching(self):
        """Тест pattern matching."""
        router = QueryRouter()

        # Благодарность
        level, conf = router.route("спасибо")
        assert level == ProcessingLevel.PATTERN

        # Прощание
        level, conf = router.route("пока")
        assert level == ProcessingLevel.PATTERN


class TestHealthCheck:
    """Тесты системы здоровья."""

    def test_health_check_initialization(self):
        """Тест инициализации."""
        hc = HealthCheck()
        assert hc is not None

    def test_check_component_healthy(self):
        """Тест проверки здорового компонента."""
        hc = HealthCheck()
        result = hc.check_component("test_component", lambda: True)
        assert result["status"] == "healthy"
        assert result["name"] == "test_component"

    def test_check_component_unhealthy(self):
        """Тест проверки нездорового компонента."""
        hc = HealthCheck()
        result = hc.check_component("bad_component", lambda: None)
        assert result["status"] == "unhealthy"

    def test_check_component_exception(self):
        """Тест проверки компонента с исключением."""
        hc = HealthCheck()

        def failing_check():
            raise Exception("Test error")

        result = hc.check_component("failing_component", failing_check)
        assert result["status"] == "unhealthy"
        assert "error" in result

    def test_record_request(self):
        """Тест записи запроса."""
        hc = HealthCheck()
        hc.record_request(0.5, success=True)
        hc.record_request(0.3, success=True)
        hc.record_request(1.0, success=False)
        # Запись должна успешно выполниться без ошибок

    def test_get_status(self):
        """Тест получения статуса."""
        hc = HealthCheck()
        hc.check_component("test", lambda: True)
        status = hc.get_status()

        assert "status" in status
        assert "components" in status
        assert "uptime_seconds" in status
        assert "timestamp" in status

    def test_overall_status_determination(self):
        """Тест определения общего статуса."""
        hc = HealthCheck()
        hc.check_component("healthy", lambda: True)
        hc.check_component("healthy2", lambda: True)

        status = hc.get_status()
        assert status["status"] == "healthy"

    def test_health_check_metrics(self):
        """Тест метрик health check."""
        hc = HealthCheck()
        metrics = hc.get_metrics()

        assert "uptime" in metrics
        assert "components" in metrics
        assert "timestamp" in metrics

    def test_multiple_components(self):
        """Тест проверки нескольких компонентов."""
        hc = HealthCheck()
        hc.check_component("comp1", lambda: True)
        hc.check_component("comp2", lambda: True)
        hc.check_component("comp3", lambda: True)

        status = hc.get_status()
        assert len(status["components"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])