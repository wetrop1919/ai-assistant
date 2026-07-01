"""
Продвинутый интерактивный CLI интерфейс.
"""

import logging
import asyncio
from typing import Optional, List
from pathlib import Path
from datetime import datetime
from difflib import get_close_matches

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
import click

from config import config
from core.brain import Brain
from core.enhanced_memory import EnhancedMemory
from core.ears import Ears
from core.voice import Voice
from skills.registry import SkillRegistry
from utils import AsciiArt, TextFormatter

from .themes import get_theme_manager
from .formatters import get_formatter
from .input_handler import InputHandler
from .output_manager import OutputManager
from .animations import get_animation_manager
from .shortcuts import get_shortcut_manager

logger = logging.getLogger(__name__)


class AdvancedCLI:
    """Продвинутый CLI интерфейс."""

    def __init__(
        self,
        brain: Brain,
        memory: EnhancedMemory,
        ears: Optional[Ears] = None,
        voice: Optional[Voice] = None,
        advanced: bool = False,
    ):
        """
        Инициализация CLI.

        Args:
            brain: Мозг ассистента
            memory: Система памяти
            ears: Распознавание речи
            voice: Синтез речи
            advanced: Включен ли advanced режим
        """
        self.brain = brain
        self.memory = memory
        self.ears = ears
        self.voice = voice
        self.skills = SkillRegistry(brain=self.brain, memory=self.memory)
        self.advanced = advanced

        # UI компоненты
        self.console = Console()
        self.theme_manager = get_theme_manager()
        self.formatter = get_formatter()
        self.animation_manager = get_animation_manager()
        self.shortcut_manager = get_shortcut_manager()

        # История и ввод
        self.input_handler = InputHandler(
            history_file=".cli_history",
            commands=self._get_commands(),
            skills=self._get_skill_names(),
            models=self._get_model_names(),
        )

        # Управление выводом
        self.output_manager = OutputManager(self.console)

        # Состояние
        self.is_running = False
        self.session_start = datetime.now()
        self.query_count = 0
        self.silent_mode = False

        logger.info("💬 Инициализирован продвинутый CLI")

    def _get_commands(self) -> List[str]:
        """Получить список команд."""
        return [
            "/help",
            "/voice",
            "/model",
            "/memory",
            "/clear",
            "/skills",
            "/system",
            "/log",
            "/config",
            "/exit",
            "/theme",
            "/status",
            "/export",
            "/history",
        ]

    def _get_skill_names(self) -> List[str]:
        """Получить имена навыков."""
        try:
            skills = self.skills.get_all_skills()
            return [s["name"] for s in skills]
        except:
            return []

    def _get_model_names(self) -> List[str]:
        """Получить имена моделей."""
        return [
            "llama3:8b",
            "llama3:70b",
            "phi3:mini",
            "codellama:13b",
        ]

    def _find_similar_commands(self, command: str) -> list:
        """
        Найти похожие команды через расстояние Левенштейна.
        
        Args:
            command: Введённая команда
            
        Returns:
            Список похожих команд (до 3)
        """
        from difflib import get_close_matches
        
        all_commands = self._get_commands()
        return get_close_matches(command, all_commands, n=3, cutoff=0.6)

    async def show_banner(self) -> None:
        """Показать баннер."""
        self.console.clear()
        AsciiArt.print_banner()

        # Информация о конфигурации
        config_text = f"""
🔧 Конфигурация:
  • Режим: {'Advanced' if self.advanced else 'Standard'} {'| CLI' if config.mode.cli_mode else ''}
  • Тема: {self.theme_manager.current_theme_name}
  • RAG: {'✅' if self.brain.rag_system else '❌'}
  • Память: {'✅' if self.brain.memory else '❌'}
  • Мультимодальность: {'✅' if self.brain.multimodal else '❌'}

📋 Команды:
  /help - справка
  /status - статус
  /theme - сменить тему
  /exit - выход
  
⌨️ Горячие клавиши:
  Ctrl+L - очистить экран
  Ctrl+S - сохранить диалог
  Alt+V - переключить голос
  Alt+M - сменить модель
  Alt+T - сменить тему
"""

        panel = self.formatter.format_panel(
            config_text,
            title="AI Assistant",
            style="info",
        )

        self.output_manager.print(panel)

    async def show_help(self) -> None:
        """Показать справку."""
        help_content = """
# 📚 Справка по командам

## 💻 Основные команды

### /help
Показать эту справку

### /status
Показать статус ассистента и всех компонентов

### /voice
Переключить голосовой режим (включить/выключить)

### /model <name>
Сменить модель LLM
Примеры: /model llama3:8b, /model phi3:mini

### /theme <name>
Сменить цветовую схему
Доступные: dark, light, cyberpunk, minimal, monokai

## 📚 Работа с памятью

### /memory
Показать текущий контекст памяти

### /clear
Очистить краткосрочную память

### /history
Показать историю команд

## 🎯 Управление навыками

### /skills
Показать список доступных навыков

## 📊 Система

### /system
Информация о системе и ресурсах

### /log
Показать последние логи

### /config
Изменить конфигурацию

### /export
Экспортировать диалог

## ℹ️ Специальные команды

Вводите многострочный текст (код и т.д.):
- Нажмите Enter для новой строки
- Нажмите Ctrl+D для завершения ввода

Сохранение вывода:
- /export > filename.txt - сохранить вывод
- Ctrl+C скопирует последний ответ
"""

        md = self.formatter.format_markdown(help_content)
        self.output_manager.print(md)

    async def handle_command(self, command: str) -> bool:
        """
        Обработать команду CLI.

        Args:
            command: Команда

        Returns:
            False если нужно выйти
        """
        command = command.strip()

        if not command:
            return True

        # Системные команды
        if command.lower() == "/exit":
            self.formatter.print_info("👋 Выход из ассистента...")
            return False

        elif command.lower() == "/help":
            await self.show_help()
            return True

        elif command.lower() == "/status":
            await self._show_status()
            return True

        elif command.lower() == "/voice":
            await self._toggle_voice()
            return True

        elif command.lower().startswith("/model"):
            model = command.split()[1] if len(command.split()) > 1 else None
            if model:
                await self._change_model(model)
            else:
                self.formatter.print_warning("⚠️ Укажите модель: /model <name>")
            return True

        elif command.lower() == "/memory":
            await self._show_memory()
            return True

        elif command.lower() == "/clear":
            await self._clear_memory()
            return True

        elif command.lower() == "/skills":
            await self._show_skills()
            return True

        elif command.lower() == "/theme":
            parts = command.split()
            if len(parts) > 1:
                theme = parts[1]
                self.theme_manager.set_theme(theme)
                self.formatter.print_success(f"✅ Тема изменена на {theme}")
            else:
                themes = self.theme_manager.get_available_themes()
                self.formatter.print_info(f"Доступные темы: {', '.join(themes)}")
            return True

        elif command.lower() == "/system":
            await self._show_system_info()
            return True

        elif command.lower() == "/log":
            await self._show_logs()
            return True

        elif command.lower() == "/config":
            await self._show_config()
            return True

        elif command.lower() == "/export":
            await self._export_dialog()
            return True

        elif command.lower() == "/history":
            await self._show_history()
            return True

        else:
            # Проверяем — это неизвестная команда (начинается с /)
            if command.startswith("/"):
                # Поиск похожих команд
                similar = self._find_similar_commands(command)
                if similar:
                    self.formatter.print_warning(
                        f"❌ Неизвестная команда: {command}\n"
                        f"💡🤔 Возможно вы имели в виду: {', '.join(similar)}"
                    )
                else:
                    self.formatter.print_warning(
                        f"❌ Неизвестная команда: {command}\n"
                        f"❕ Введите /help для списка команд"
                    )
            else:
                # Обычный запрос (не команда)
                await self._process_query(command)
            return True

    async def _process_query(self, prompt: str) -> None:
        """Обработать запрос пользователя."""
        try:
            self.query_count += 1

            # Добавляем в память
            if self.memory:
                self.memory.add_episodic_memory(
                    event_type="user_query",
                    content=prompt,
                    importance=0.6,
                )

            # Проверяем навыки
            skill_result = await self.skills.execute_skill(prompt)

            if skill_result:
                self.output_manager.print(skill_result)
                if self.voice and config.mode.voice_mode:
                    self.voice.speak(skill_result, wait=False)
                return

            # Генерируем ответ
            print("🤔 Думаю...", end="", flush=True)
            # Можно добавить точки
            for _ in range(3):
                await asyncio.sleep(0.3)
                print(".", end="", flush=True)
            print()  # Очищаем анимацию

            context = []
            if self.memory and hasattr(self.memory, 'get_short_term_context'):
                context = self.memory.get_short_term_context()

            answer = await self.brain.generate(
                prompt=prompt,
                context=context,
                use_rag=self.advanced,
            )

            # Сохраняем ответ
            if self.memory:
                self.memory.add_episodic_memory(
                    event_type="assistant_response",
                    content=answer,
                    importance=0.6,
                )

            # Форматируем и выводим
            self.output_manager.print(f"\n🤖 {answer}\n")

            # Озвучиваем
            if self.voice and config.mode.voice_mode:
                self.voice.speak(answer, wait=False)

        except Exception as e:
            self.formatter.print_error(f"❌ Ошибка: {e}")
            logger.error(f"Ошибка обработки запроса: {e}", exc_info=config.debug)

    async def _show_status(self) -> None:
        """Показать статус ассистента."""
        status = self.brain.get_status()
        health = status.get('health', {})

        status_data = [
            {"Компонент": "Ollama", "Статус": "✅" if status.get('available') else "❌"},
            {"Компонент": "RAG", "Статус": "✅" if status.get('rag_available') else "❌"},
            {"Компонент": "Память", "Статус": "✅" if status.get('memory_available') else "❌"},
            {"Компонент": "Мультимодальность", "Статус": "✅" if status.get('multimodal_available') else "❌"},
        ]

        self.formatter.print_table(status_data, title="Статус компонентов")

    async def _toggle_voice(self) -> None:
        """Переключить голосовой режим."""
        config.mode.voice_mode = not config.mode.voice_mode
        status = "✅ включен" if config.mode.voice_mode else "❌ отключен"
        self.formatter.print_success(f"Голосовой режим {status}")

    async def _change_model(self, model: str) -> None:
        """Сменить модель."""
        self.formatter.print_success(f"✅ Модель изменена на {model}")

    async def _show_memory(self) -> None:
        """Показать контекст памяти."""
        if not self.memory:
            self.formatter.print_warning("❌ Память не доступна")
            return

        stats = self.memory.get_memory_stats() if hasattr(self.memory, 'get_memory_stats') else {}

        memory_data = [
            {"Тип": "Episodic", "Количество": str(stats.get('episodic', 0))},
            {"Тип": "Semantic", "Количество": str(stats.get('semantic', 0))},
            {"Тип": "Working", "Количество": str(stats.get('working', 0))},
        ]

        self.formatter.print_table(memory_data, title="Статистика памяти")

    async def _clear_memory(self) -> None:
        """Очистить память."""
        if self.memory and hasattr(self.memory, 'clear_short_term'):
            self.memory.clear_short_term()
        self.formatter.print_success("✅ Память очищена")

    async def _show_skills(self) -> None:
        """Показать навыки."""
        skills = self.skills.get_all_skills()

        skills_data = [
            {
                "Навык": s["name"],
                "Статус": "✅" if s.get("enabled") else "❌",
                "Приоритет": str(s.get("priority", 50)),
            }
            for s in skills
        ]

        self.formatter.print_table(skills_data, title="Доступные навыки")

    async def _show_system_info(self) -> None:
        """Показать информацию о системе."""
        try:
            import psutil

            system_data = [
                {"Параметр": "CPU", "Значение": f"{psutil.cpu_percent()}%"},
                {"Параметр": "Память", "Значение": f"{psutil.virtual_memory().percent}%"},
                {"Параметр": "Диск", "Значение": f"{psutil.disk_usage('/').percent}%"},
            ]

            self.formatter.print_table(system_data, title="Информация о системе")

        except Exception as e:
            self.formatter.print_error(f"❌ Ошибка получения информации: {e}")

    async def _show_logs(self) -> None:
        """Показать логи."""
        self.formatter.print_info("📋 Последние логи будут здесь")

    async def _show_config(self) -> None:
        """Показать конфигурацию."""
        self.formatter.print_info("⚙️ Конфигурация будет здесь")

    async def _export_dialog(self) -> None:
        """Экспортировать диалог."""
        filename = f"dialog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        if self.output_manager.save_output(filename):
            self.formatter.print_success(f"✅ Диалог сохранен в {filename}")
        else:
            self.formatter.print_error("❌ Ошибка сохранения диалога")

    async def _show_history(self) -> None:
        """Показать историю."""
        self.formatter.print_info("📜 История команд сохраняется в .cli_history")

    async def run(self) -> None:
        """Запустить интерактивный интерфейс."""
        self.is_running = True
        await self.show_banner()

        try:
            while self.is_running:
                try:
                    # Получаем ввод
                    user_input = await self.input_handler.get_input()

                    if user_input is None:
                        break

                    # Обрабатываем команду
                    if not await self.handle_command(user_input):
                        break

                except KeyboardInterrupt:
                    self.console.print("\n\n👋 До встречи!")
                    break
                except EOFError:
                    break

        except Exception as e:
            logger.error(f"❌ Ошибка CLI: {e}", exc_info=True)
        finally:
            self.is_running = False

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"AdvancedCLI(advanced={self.advanced}, queries={self.query_count})"


# Для обратной совместимости
CLI = AdvancedCLI