"""
Финальная версия AI Assistant.

Быстрый старт:
    python main.py --cli                    # Текстовый режим
    python main.py --voice                  # Голосовой режим
    python main.py --server --port 8000     # REST API сервер
    python main.py --daemon                 # Фоновый сервис
"""

import asyncio
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional
import signal
import traceback

from rich.console import Console

from logger import setup_logger, get_logger
from config import config, AppConfig
from core.brain import Brain
from core.enhanced_memory import EnhancedMemory
from ui.cli import AdvancedCLI
from integrations import init_manager
from utils import AsciiArt, ProgressBar

# Инициализируем логирование
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
        self.brain: Optional[Brain] = None
        self.memory: Optional[EnhancedMemory] = None
        self.cli: Optional[AdvancedCLI] = None
        self.running = False

        self._setup_logging()
        self._setup_security()

    def _setup_logging(self) -> None:
        """Настроить логирование."""
        log_level = "DEBUG" if self.args.debug else "INFO"
        setup_logger(log_level=log_level)

        logger.info("=" * 70)
        logger.info(f"🚀 Запуск AI Assistant v{config.version}")
        logger.info(f"   Режим: {self.args.mode}")
        logger.info(f"   Sandbox: {self.args.sandbox}")
        logger.info(f"   Debug: {self.args.debug}")
        logger.info(f"   Advanced: {self.args.advanced}")
        logger.info("=" * 70)

    def _setup_security(self) -> None:
        """Настроить безопасность."""
        from security.policies import PolicyManager, PolicyProfile

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
                    enable_rag=self.args.advanced,
                    enable_multimodal=self.args.advanced,
                )
                pbar.update(50)

                try:
                    if hasattr(self.brain, 'check_connection'):
                        self.brain.check_connection()
                    pbar.update(100)
                except Exception as e:
                    logger.error(f"❌ Ollama недоступна: {e}")
                    print("\n💡 Убедитесь, что Ollama запущена:")
                    print("   ollama serve")
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
                    advanced=self.args.advanced,
                )

            elif self.args.mode == "server":
                await self._init_server()

            elif self.args.mode == "voice":
                from ui.voice_cli import VoiceCLI
                
                self.voice_cli = VoiceCLI(
                    brain=self.brain,
                    memory=self.memory,
                )
                
            elif self.args.mode == "daemon":
                await self._init_daemon()

            logger.info("✅ Инициализация завершена")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}", exc_info=True)
            traceback.print_exc()
            return False

    async def _init_server(self) -> None:
        """Инициализировать REST API сервер."""
        try:
            from api.server import APIServer

            port = self.args.port or 8000
            self.server = APIServer(self.brain, self.memory, port=port)
            logger.info(f"🌐 API сервер готов на http://localhost:{port}")
        except ImportError:
            logger.warning("⚠️ API сервер не доступен")

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
                if self.cli:
                    await self.cli.run()

            elif self.args.mode == "voice":
                await self._run_voice_mode()

            elif self.args.mode == "server":
                await self._run_server_mode()
                
            elif self.args.mode == "voice":
                if hasattr(self, 'voice_cli'):
                    await self.voice_cli.run()

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
        await asyncio.sleep(1)

    async def _run_server_mode(self) -> None:
        """Запустить серверный режим."""
        port = self.args.port or 8000
        print(f"\n🌐 Сервер запущен на http://localhost:{port}")
        print("Ctrl+C для остановки")

        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass

    async def _run_daemon_mode(self) -> None:
        """Запустить режим демона."""
        print("\n🌙 Демон работает в фоне")

        try:
            while self.running:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            pass

    async def shutdown(self) -> None:
        """Завершить работу."""
        logger.info("🏁 Завершение работы...")
        self.running = False

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
  python main.py --mode cli                      # Текстовый режим (по умолчанию)
  python main.py --mode cli --advanced           # Текстовый режим с Advanced
  python main.py --mode voice                    # Голосовой режим
  python main.py --mode server --port 8000       # REST API
  python main.py --mode daemon                   # Фоновый режим
  python main.py --sandbox strict                # Максимальная безопасность
  python main.py --debug                         # Режим отладки
  python main.py --profile                       # Профилирование
        """,
    )

    # Режим
    parser.add_argument(
        "--mode",
        choices=["cli", "voice", "server", "daemon"],
        default="cli",
        help="Режим работы (по умолчанию: cli)",
    )

    # Advanced
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Включить Advanced режим (RAG + Multimodal)",
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
        version=f"%(prog)s {config.version}",
    )

    return parser.parse_args()


def main() -> None:
    """Главная функция."""
    try:
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
        asyncio.run(assistant.run())

    except KeyboardInterrupt:
        logger.info("👋 До встречи!")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()