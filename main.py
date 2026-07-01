"""
Обновленная точка входа с новыми флагами.
"""

import asyncio
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional
import signal
import os

import yaml
from rich.console import Console

from logger import setup_logger, get_logger
from config import Config
from core.brain import Brain
from core.enhanced_memory import EnhancedMemory
from core.ears import Ears
from core.voice import Voice
from core.security import SecurityManager
from security.policies import PolicyManager, PolicyProfile
from ui.cli import AdvancedCLI
from ui.themes import get_theme_manager
from integrations import init_manager
from utils import AsciiArt, ProgressBar

setup_logger(
    log_level=config.logging.log_level,
    log_file=config.logging.log_file,
    log_format=config.logging.log_format,
)

logger = get_logger(__name__)
console = Console()

class Assistant:
    """Главный класс ассистента."""

    def __init__(self, args: argparse.Namespace):
        """
        Инициализация ассистента.

        Args:
            args: Аргументы командной строки
        """
        self.args = args
        self.config = self._load_config(args.config)
        self.brain: Optional[Brain] = None
        self.memory: Optional[EnhancedMemory] = None
        self.cli: Optional[AdvancedCLI] = None
        self.running = False

        self._setup_logging()
        self._setup_security()

    def _load_config(self, config_path: str) -> Config:
        """Загрузить конфигурацию."""
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            logger.info(f"✅ Конфигурация загружена: {config_path}")
            return Config(**config_data)

        except FileNotFoundError:
            logger.warning(f"⚠️ Конфиг не найден: {config_path}, используем defaults")
            from config import config
            return config

    def _setup_logging(self) -> None:
        """Настроить логирование."""
        log_level = "DEBUG" if self.args.debug else "INFO"
        setup_logger(log_level=log_level)

        logger.info("=" * 70)
        logger.info(f"🚀 Запуск AI Assistant v{self.config.version}")
        logger.info(f"   Режим: {self.args.mode}")
        logger.info(f"   Sandbox: {self.args.sandbox}")
        logger.info(f"   Debug: {self.args.debug}")
        logger.info("=" * 70)

    def _setup_security(self) -> None:
        """Настроить безопасность."""
        sandbox_levels = {
            "strict": PolicyProfile.STRICT,
            "balanced": PolicyProfile.BALANCED,
            "permissive": PolicyProfile.PERMISSIVE,
            "off": None,
        }

        profile = sandbox_levels.get(self.args.sandbox, PolicyProfile.BALANCED)

        if profile:
            policy_manager = PolicyManager(profile)
            logger.info(f"🔒 Политика безопасности: {profile.value}")
        else:
            logger.warning("⚠️ Безопасность отключена!")

    async def initialize(self) -> bool:
        """
        Инициализировать компоненты.

        Returns:
            True если успешно
        """
        try:
            console.clear()
            AsciiArt.print_banner()

            # 1. Мозг
            print("\n1️⃣  Инициализация мозга...")
            with ProgressBar.create_bar_manual(total=100, desc="Brain") as pbar:
                self.brain = Brain(
                    enable_rag=self.args.mode != "voice",
                    enable_multimodal=self.args.mode != "voice",
                )
                pbar.update(50)

                try:
                    self.brain.check_connection()
                    pbar.update(100)
                except Exception as e:
                    logger.error(f"❌ Ollama недоступна: {e}")
                    return False

            # 2. Память
            print("\n2️⃣  Инициализация памяти...")
            with ProgressBar.create_bar_manual(total=100, desc="Memory") as pbar:
                self.memory = self.brain.memory or EnhancedMemory()
                pbar.update(100)

            # 3. Интеграции
            print("\n3️⃣  Инициализация интеграций...")
            init_manager(sandbox_mode=self.args.sandbox != "off")

            # 4. Режим-специфичная инициализация
            print(f"\n4️⃣  Инициализация режима {self.args.mode}...")

            if self.args.mode in ["cli", "voice"]:
                self.cli = AdvancedCLI(
                    brain=self.brain,
                    memory=self.memory,
                    advanced=self.args.model == "auto",
                )

            elif self.args.mode == "server":
                await self._init_server()

            elif self.args.mode == "daemon":
                await self._init_daemon()

            logger.info("✅ Инициализация завершена")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}", exc_info=True)
            return False

    async def _init_server(self) -> None:
        """Инициализировать REST API сервер."""
        from api.server import APIServer

        port = self.args.port or 8000
        self.server = APIServer(self.brain, self.memory, port=port)
        logger.info(f"🌐 API сервер готов на http://localhost:{port}")

    async def _init_daemon(self) -> None:
        """Инициализировать фоновый сервис."""
        logger.info("🌙 Фоновый режим активирован")

    async def run(self) -> None:
        """Запустить ассистент."""
        self.running = True

        try:
            # Инициализируем
            if not await self.initialize():
                return

            # Запускаем режим
            if self.args.mode == "cli":
                await self.cli.run()

            elif self.args.mode == "voice":
                await self._run_voice_mode()

            elif self.args.mode == "server":
                await self._run_server_mode()

            elif self.args.mode == "daemon":
                await self._run_daemon_mode()

        except KeyboardInterrupt:
            logger.info("⏹️ Остановка по Ctrl+C")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def _run_voice_mode(self) -> None:
        """Запустить голосовой режим."""
        print("\n🎤 Голосовой режим активирован")
        print("Слушаю... (Ctrl+C для выхода)")

        # Здесь будет голосовой интерфейс
        # Пока имитируем
        await asyncio.sleep(1)

    async def _run_server_mode(self) -> None:
        """Запустить серверный режим."""
        print(f"\n🌐 Сервер запущен на http://localhost:{self.args.port or 8000}")
        print("Ctrl+C для остановки")

        # Бесконечный цикл
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass

    async def _run_daemon_mode(self) -> None:
        """Запустить режим демона."""
        print("\n🌙 Демон работает в фоне")

        # Бесконечный цикл для фонового процесса
        try:
            while self.running:
                # Индексация, бэкапы и т.д.
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            pass

    async def shutdown(self) -> None:
        """Завершить работу."""
        logger.info("🏁 Завершение работы...")
        self.running = False

        # Сохраняем состояние
        if self.memory:
            logger.info("💾 Сохранение памяти...")

        logger.info("=" * 70)
        logger.info("👋 До встречи!")
        logger.info("=" * 70)


def parse_arguments() -> argparse.Namespace:
    """Парсить аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="🤖 AI Assistant - Персональный AI ассистент",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  assistant run --mode cli                      # Текстовый режим
  assistant run --mode voice                    # Голосовой режим
  assistant run --mode server --port 8000       # REST API
  assistant run --mode daemon                   # Фоновый режим
  assistant run --sandbox strict                # Максимальная безопасность
  assistant run --debug                         # Режим отладки
  assistant run --profile                       # Профилирование
        """,
    )

    # Режим
    parser.add_argument(
        "--mode",
        choices=["cli", "voice", "server", "daemon"],
        default="cli",
        help="Режим работы (по умолчанию: cli)",
    )

    # Безопасность
    parser.add_argument(
        "--sandbox",
        choices=["strict", "balanced", "permissive", "off"],
        default="balanced",
        help="Уровень безопасности (по умолчанию: balanced)",
    )

    # Модель
    parser.add_argument(
        "--model",
        default="auto",
        help="Модель LLM (по умолчанию: auto)",
    )

    # Конфигурация
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Файл конфигурации (по умолчанию: config.yaml)",
    )

    # Рабочее пространство
    parser.add_argument(
        "--workspace",
        default="~/assistant_workspace",
        help="Рабочая директория (по умолчанию: ~/assistant_workspace)",
    )

    # Порт (для server режима)
    parser.add_argument(
        "--port",
        type=int,
        help="Порт для server режима (по умолчанию: 8000)",
    )

    # Отладка
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Режим отладки",
    )

    # Профилирование
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Профилирование производительности",
    )

    # Версия
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.2.0",
    )

    return parser.parse_args()


def main() -> None:
    """Главная функция."""
    args = parse_arguments()

    # Создаем и запускаем ассистент
    assistant = Assistant(args)

    # Обработчик сигналов
    def signal_handler(sig, frame):
        logger.info("⏹️ Получен сигнал завершения")
        asyncio.create_task(assistant.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Запускаем асинхронный цикл
    try:
        asyncio.run(assistant.run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()