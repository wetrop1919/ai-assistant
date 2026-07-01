"""
Улучшенный мозг ассистента с RAG, маршрутизацией и мультимодальностью.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import requests

from config import config
from .rag import RAGSystem
from .router import QueryRouter, ProcessingLevel
from .enhanced_memory import EnhancedMemory
from .multimodal import MultimodalProcessor
from .self_check import HealthCheck
from utils import retry, TextFormatter
try:
    from integrations import init_manager, get_manager
except ImportError:
    def init_manager(*args, **kwargs):
        return None
    def get_manager():
        return None
from core.security import SecurityManager
from security.policies import PolicyManager, PolicyProfile
from security.confirmation import ConfirmationManager
from security.recovery import RecoveryManager

logger = logging.getLogger(__name__)


class Brain:
    """
    Улучшенный мозг ассистента.

    Включает:
    - RAG для поиска контекста
    - Интеллектуальную маршрутизацию запросов
    - Расширенную память
    - Мультимодальность
    - Самодиагностику
    """

    SYSTEM_PROMPT_RU = """Ты - персональный AI ассистент на русском языке.
Ты дружелюбный, полезный и всегда стараешься помочь пользователю.
Отвечай кратко и по сути.
Используй эмодзи для улучшения читаемости.

Твои особенности:
- Помнишь контекст диалога
- Учишь предпочтения пользователя
- Помогаешь разными способами (код, объяснения, планы)
- Честный - говоришь если что-то не знаешь
"""

    def __init__(self, enable_rag: bool = False, enable_multimodal: bool = False):
        """
        Инициализация мозга.

        Args:
            enable_rag: Включить RAG
            enable_multimodal: Включить мультимодальность
        """
        self.ollama_host = config.ollama.host
        self.default_model = config.ollama.model
        self.code_model = config.ollama.code_model
        self.fast_model = config.ollama.fast_model
        self.timeout = config.ollama.timeout

        # RAG система
        self.rag_system: Optional[RAGSystem] = None
        if enable_rag:
            try:
                self.rag_system = RAGSystem()
            except Exception as e:
                logger.warning(f"⚠️ RAG не инициализирована: {e}")

        # Маршрутизатор
        self.router = QueryRouter()

        # Расширенная память
        self.memory: Optional[EnhancedMemory] = None
        try:
            self.memory = EnhancedMemory(rag_system=self.rag_system)
        except Exception as e:
            logger.warning(f"⚠️ Расширенная память не инициализирована: {e}")

        # Мультимодальность
        self.multimodal: Optional[MultimodalProcessor] = None
        if enable_multimodal:
            self.multimodal = MultimodalProcessor(brain=self)

        # Здоровье
        self.health = HealthCheck()

        # Состояние
        self.is_available = False
        self._session: Optional[requests.Session] = None

        logger.info(f"🧠 Инициализация улучшенного Brain")
        logger.info(f"   RAG: {'✅' if self.rag_system else '❌'}")
        logger.info(f"   Память: {'✅' if self.memory else '❌'}")
        logger.info(f"   Multimodal: {'✅' if self.multimodal else '❌'}")
        
        # Инициализируем менеджер интеграций
        self.integration_manager = init_manager(
            sandbox_mode=config.mode.sandbox_mode
        )

        # Регистрируем интеграции
        self._register_integrations()

        logger.info("🔌 Интеграции инициализированы")
        
        self.security_manager = SecurityManager(
            sandbox_enabled=config.mode.sandbox_mode,
            workspace=config.security.workspace_dir,
        )

        self.policy_manager = PolicyManager()
        self.confirmation_manager = ConfirmationManager()
        self.recovery_manager = RecoveryManager()

        logger.info("🔒 Безопасность инициализирована")


    def _register_integrations(self) -> None:
        """Зарегистрировать интеграции."""
        from integrations.calendar import CalendarIntegration
        from integrations.email_client import EmailIntegration
        from integrations.todo_manager import TodoIntegration
        from integrations.smart_home import SmartHomeIntegration
        from integrations.media_controller import MediaIntegration
        from integrations.notifier import NotifierIntegration

        # Регистрируем только если включены
        if config.integrations.CALENDAR_ENABLED:
            self.integration_manager.register(
                "calendar",
                CalendarIntegration(config.integrations.dict()),
            )

        if config.integrations.EMAIL_ENABLED:
            self.integration_manager.register(
                "email",
                EmailIntegration(config.integrations.dict()),
            )

        if config.integrations.TODO_ENABLED:
            self.integration_manager.register(
                "todo",
                TodoIntegration(config.integrations.dict()),
            )

        if config.integrations.SMART_HOME_ENABLED:
            self.integration_manager.register(
                "smart_home",
                SmartHomeIntegration(config.integrations.dict()),
            )

        if config.integrations.MEDIA_ENABLED:
            self.integration_manager.register(
                "media",
                MediaIntegration(config.integrations.dict()),
            )

        if config.integrations.NOTIFIER_ENABLED:
            self.integration_manager.register(
                "notifier",
                NotifierIntegration(config.integrations.dict()),
            )
    
    def _get_session(self) -> requests.Session:
        """Получить сессию requests."""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    @retry(max_attempts=3, delay=1.0)
    def check_connection(self) -> bool:
        """Проверить доступность Ollama."""
        try:
            response = requests.get(
                f"{self.ollama_host}/api/tags",
                timeout=5,
            )

            if response.status_code == 200:
                logger.info("✅ Ollama доступна")
                self.is_available = True

                # Проверяем наличие моделей
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                logger.info(f"   Загруженные модели: {', '.join(models)}")

                # Health check
                self.health.check_component(
                    "ollama",
                    lambda: response.status_code == 200,
                )
                return True

        except Exception as e:
            error_msg = (
                f"❌ Не удалось подключиться к Ollama на {self.ollama_host}\n"
                f"Убедитесь, что Ollama запущена:\n"
                f"  1. ollama serve\n"
                f"  2. ollama pull llama3:8b"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return False

    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True,
        max_tokens: int = 500,
    ) -> str:
        """
        Генерировать ответ с учетом всех возможностей.

        Args:
            prompt: Текст запроса
            context: Контекст диалога
            use_rag: Использовать RAG
            max_tokens: Максимум токенов

        Returns:
            Сгенерированный ответ
        """
        if not self.is_available:
            raise RuntimeError("❌ Ollama не доступна")

        start_time = datetime.now()

        try:
            # 1. Маршрутизируем запрос
            level, confidence = self.router.route(prompt)
            logger.debug(
                f"🚦 Маршрутизация: {level.name} "
                f"(уверенность: {confidence:.2f})"
            )

            # 2. Получаем контекст из RAG
            rag_context = ""
            if use_rag and self.rag_system:
                rag_context = self.rag_system.get_context(prompt)
                logger.debug("📚 RAG контекст получен")

            # 3. Обогащаем контекст памятью
            memory_context = ""
            if self.memory:
                working_mem = self.memory.get_working_memory()
                if working_mem:
                    memory_context = "⚡ Текущий контекст: " + \
                        " | ".join([m.get("content", "")[:50] for m in working_mem[:3]])

            # 4. Выбираем модель
            model = self.router.get_model_for_level(level)
            if model.startswith(("phi3", "llama3", "codellama")):
                model = config.ollama.model  # Используем конфигурированную модель

            # 5. Формируем полный контекст
            full_context = ""
            if rag_context:
                full_context += rag_context + "\n"
            if memory_context:
                full_context += memory_context + "\n"

            # 6. Генерируем ответ
            messages = context or []
            if full_context:
                messages = messages + [{
                    "role": "system",
                    "content": full_context,
                }]
            messages.append({"role": "user", "content": prompt})

            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "system": self.SYSTEM_PROMPT_RU,
                    "stream": False,
                    "temperature": self._get_temperature_for_level(level),
                    "num_predict": max_tokens,
                },
                timeout=self.timeout,
            )

            if response.status_code != 200:
                raise RuntimeError(f"Ollama ошибка: {response.text}")

            answer = response.json().get("message", {}).get("content", "").strip()

            # 7. Сохраняем в память
            if self.memory:
                self.memory.add_episodic_memory(
                    event_type="query_response",
                    content=prompt,
                    importance=confidence,
                )
                self.memory.add_working_memory(answer)

            # 8. Записываем метрику
            duration = (datetime.now() - start_time).total_seconds()
            self.health.record_request(duration, success=True)

            logger.debug(
                f"✅ Ответ сгенерирован за {duration:.2f}s "
                f"(модель: {model})"
            )

            return answer

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.health.record_request(duration, success=False)
            logger.error(f"❌ Ошибка генерации: {e}")
            raise

    async def execute_code_safely(self, code: str) -> Tuple[bool, str]:
        """Безопасно выполнить код."""
        return await self.security_manager.execute_code(code)

    def validate_command_safety(self, command: str) -> Tuple[bool, str, str]:
        """Валидировать команду."""
        valid, level, reason = self.security_manager.validate_command(command)
        return valid, level.name, reason

    def get_security_status(self) -> Dict[str, Any]:
        """Получить статус безопасности."""
        return self.security_manager.get_security_status()

    def _get_temperature_for_level(self, level: ProcessingLevel) -> float:
        """Получить температуру для уровня."""
        temp_map = {
            ProcessingLevel.COMMAND: 0.0,
            ProcessingLevel.PATTERN: 0.3,
            ProcessingLevel.LIGHT: 0.5,
            ProcessingLevel.GENERAL: config.ollama.temperature_general,
            ProcessingLevel.COMPLEX: 0.8,
            ProcessingLevel.CODE: config.ollama.temperature_code,
        }
        return temp_map.get(level, config.ollama.temperature_general)

    def get_status(self) -> Dict[str, Any]:
        """Получить статус мозга."""
        return {
            "available": self.is_available,
            "ollama_host": self.ollama_host,
            "default_model": self.default_model,
            "rag_available": self.rag_system is not None,
            "memory_available": self.memory is not None,
            "multimodal_available": self.multimodal is not None,
            "health": self.health.get_status(),
        }

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"Brain(available={self.is_available}, rag={self.rag_system is not None})"