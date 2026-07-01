"""
Менеджер интеграций для подключения внешних сервисов.

Предоставляет единый интерфейс для всех интеграций с:
- Ленивой загрузкой
- Кешированием
- Rate limiting
- Fallback механизмом
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Статус сервиса."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class IntegrationError(Exception):
    """Базовый класс ошибок интеграции."""
    pass


class RateLimiter:
    """Простой rate limiter."""

    def __init__(self, max_calls: int = 10, period: int = 60):
        """
        Инициализация rate limiter.

        Args:
            max_calls: Максимум вызовов
            period: Период в секундах
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: List[datetime] = []

    async def __aenter__(self):
        """Асинхронный контекст менеджер."""
        now = datetime.now()
        self.calls = [c for c in self.calls if c > now - timedelta(seconds=self.period)]

        if len(self.calls) >= self.max_calls:
            sleep_time = (self.calls[0] - (now - timedelta(seconds=self.period))).total_seconds()
            if sleep_time > 0:
                logger.debug(f"⏱️ Rate limit: ожидаю {sleep_time:.1f}с")
                await asyncio.sleep(sleep_time)

        self.calls.append(datetime.now())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста."""
        pass


class Cache:
    """Простой кеш с TTL."""

    def __init__(self, ttl: int = 300):
        """
        Инициализация кеша.

        Args:
            ttl: Time to live в секундах
        """
        self.ttl = ttl
        self.data: Dict[str, tuple] = {}

    def get(self, key: str) -> Optional[Any]:
        """Получить из кеша."""
        if key in self.data:
            value, timestamp = self.data[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return value
            else:
                del self.data[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Установить в кеш."""
        self.data[key] = (value, datetime.now())

    def clear(self) -> None:
        """Очистить кеш."""
        self.data.clear()


def cached(ttl: int = 300):
    """Декоратор кеширования."""
    cache = Cache(ttl=ttl)

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached_value = cache.get(cache_key)

            if cached_value is not None:
                logger.debug(f"💾 Кеш попал: {func.__name__}")
                return cached_value

            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        return async_wrapper
    return decorator


class BaseIntegration:
    """Базовый класс для всех интеграций."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация интеграции.

        Args:
            name: Имя интеграции
            config: Конфигурация
        """
        self.name = name
        self.config = config or {}
        self.status = ServiceStatus.UNKNOWN
        self._initialized = False
        self.rate_limiter = RateLimiter(
            max_calls=self.config.get("rate_limit_calls", 10),
            period=self.config.get("rate_limit_period", 60),
        )

        logger.info(f"🔌 Инициализирована интеграция: {name}")

    async def initialize(self) -> bool:
        """
        Инициализировать интеграцию.

        Returns:
            True если успешно
        """
        try:
            await self._init()
            self._initialized = True
            self.status = ServiceStatus.AVAILABLE
            logger.info(f"✅ {self.name} инициализирована")
            return True

        except Exception as e:
            logger.warning(f"⚠️ {self.name} недоступна: {e}")
            self.status = ServiceStatus.UNAVAILABLE
            return False

    async def _init(self) -> None:
        """Переопределить в подклассе."""
        pass

    async def health_check(self) -> bool:
        """Проверка здоровья сервиса."""
        try:
            if not self._initialized:
                return await self.initialize()
            return True
        except Exception as e:
            logger.error(f"❌ Health check ошибка {self.name}: {e}")
            self.status = ServiceStatus.UNAVAILABLE
            return False

    def get_status(self) -> Dict[str, Any]:
        """Получить статус."""
        return {
            "name": self.name,
            "status": self.status.value,
            "initialized": self._initialized,
            "config_keys": list(self.config.keys()),
        }

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"{self.__class__.__name__}(name={self.name}, status={self.status.value})"


class IntegrationManager:
    """Менеджер интеграций."""

    def __init__(self, sandbox_mode: bool = False):
        """
        Инициализация менеджера.

        Args:
            sandbox_mode: Режим песочницы
        """
        self.sandbox_mode = sandbox_mode
        self.integrations: Dict[str, BaseIntegration] = {}
        self._loading: Dict[str, asyncio.Future] = {}

        logger.info("🔌 Инициализирован IntegrationManager")

    def register(self, name: str, integration: BaseIntegration) -> None:
        """Зарегистрировать интеграцию."""
        self.integrations[name] = integration
        logger.debug(f"✅ Зарегистрирована интеграция: {name}")

    async def get_integration(self, name: str) -> Optional[BaseIntegration]:
        """
        Получить интеграцию (с ленивой загрузкой).

        Args:
            name: Имя интеграции

        Returns:
            Интеграция если найдена
        """
        if name not in self.integrations:
            logger.warning(f"⚠️ Интеграция не найдена: {name}")
            return None

        integration = self.integrations[name]

        # Если уже инициализирована
        if integration._initialized:
            return integration

        # Если инициализируется
        if name in self._loading:
            await self._loading[name]
            return integration

        # Инициализируем
        future = asyncio.get_event_loop().create_future()
        self._loading[name] = future

        try:
            if await integration.initialize():
                future.set_result(True)
                return integration
            else:
                future.set_result(False)
                return None

        except Exception as e:
            future.set_exception(e)
            return None

        finally:
            del self._loading[name]

    async def get_all_statuses(self) -> Dict[str, Any]:
        """Получить статусы всех интеграций."""
        statuses = {}
        for name, integration in self.integrations.items():
            statuses[name] = integration.get_status()
        return statuses

    async def health_check_all(self) -> Dict[str, bool]:
        """Проверить здоровье всех интеграций."""
        results = {}
        for name, integration in self.integrations.items():
            results[name] = await integration.health_check()
        return results

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"IntegrationManager("
            f"integrations={len(self.integrations)}, "
            f"sandbox={self.sandbox_mode})"
        )


# Глобальный менеджер
manager: Optional[IntegrationManager] = None


def init_manager(sandbox_mode: bool = False) -> IntegrationManager:
    """Инициализировать глобальный менеджер."""
    global manager
    manager = IntegrationManager(sandbox_mode=sandbox_mode)
    return manager


def get_manager() -> IntegrationManager:
    """Получить глобальный менеджер."""
    global manager
    if manager is None:
        manager = IntegrationManager()
    return manager