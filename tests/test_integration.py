"""
Интеграционные тесты всей системы.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Мокируем зависимости перед импортом
sys.modules['chromadb'] = MagicMock()
sys.modules['chromadb.config'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()

# Импортируем после добавления пути и мокирования
from core.router import QueryRouter
from integrations import IntegrationManager, BaseIntegration, Cache, RateLimiter


class TestCache:
    """Тесты кеша."""

    def test_cache_set_get(self):
        """Тест установки и получения."""
        cache = Cache(ttl=300)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_cache_expiration(self):
        """Тест истечения кеша."""
        import time

        cache = Cache(ttl=1)
        cache.set("key", "value")
        time.sleep(1.1)
        assert cache.get("key") is None


class TestRateLimiter:
    """Тесты rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter(self):
        """Тест rate limiter."""
        limiter = RateLimiter(max_calls=2, period=1)

        async with limiter:
            pass  # Первый вызов

        async with limiter:
            pass  # Второй вызов

        # Третий вызов должен ждать


class TestIntegrationManager:
    """Тесты менеджера интеграций."""

    def test_manager_initialization(self):
        """Тест инициализации."""
        manager = IntegrationManager()
        assert manager is not None

    def test_register_integration(self):
        """Тест регистрации."""

        class TestIntegration(BaseIntegration):
            async def _init(self):
                pass

        manager = IntegrationManager()
        integration = TestIntegration("test")
        manager.register("test", integration)

        assert "test" in manager.integrations

    @pytest.mark.asyncio
    async def test_integration_status(self):
        """Тест статуса."""

        class TestIntegration(BaseIntegration):
            async def _init(self):
                pass

        manager = IntegrationManager()
        integration = TestIntegration("test")
        manager.register("test", integration)

        statuses = await manager.get_all_statuses()
        assert "test" in statuses
        

class TestQueryRouterIntegration:
    """Интеграционные тесты маршрутизатора."""

    def test_router_with_various_queries(self):
        """Тест маршрутизатора с различными запросами."""
        router = QueryRouter()

        test_cases = [
            ("/help", ProcessingLevel.COMMAND),
            ("привет", ProcessingLevel.PATTERN),
            ("спасибо", ProcessingLevel.PATTERN),
            ("Напиши код на Python", ProcessingLevel.CODE),
            ("Что такое ИИ?", None),  # Может быть LIGHT или GENERAL
        ]

        from core.router import ProcessingLevel as PL

        for query, expected_level in test_cases:
            level, confidence = router.route(query)
            assert level is not None
            assert 0 <= confidence <= 1
            if expected_level:
                assert level == expected_level


class TestE2E:
    """End-to-end тесты."""

    @pytest.mark.asyncio
    async def test_query_workflow(self):
        """Тест полного цикла обработки запроса."""
        from core.router import QueryRouter

        router = QueryRouter()

        # Тестируем маршрутизацию
        level, confidence = router.route("Помоги мне с Python кодом")
        assert level is not None
        assert confidence > 0

    def test_router_consistency(self):
        """Тест консистентности маршрутизатора."""
        from core.router import QueryRouter

        router = QueryRouter()

        # Один и тот же запрос должен давать один результат
        level1, conf1 = router.route("Это тестовый запрос")
        level2, conf2 = router.route("Это тестовый запрос")

        assert level1 == level2
        assert conf1 == conf2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])