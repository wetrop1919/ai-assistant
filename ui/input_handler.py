"""
Обработка пользовательского ввода с поддержкой автодополнения.
"""

import logging
from typing import List, Optional, Callable
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter, WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers import get_lexer_by_name

from .themes import get_theme_manager

logger = logging.getLogger(__name__)


class CommandCompleter(Completer):
    """Автодополнение для команд."""

    def __init__(
        self,
        commands: List[str],
        skills: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
    ):
        """
        Инициализация.

        Args:
            commands: Список команд
            skills: Список навыков
            models: Список моделей
        """
        self.commands = commands
        self.skills = skills or []
        self.models = models or []

    def get_completions(self, document, complete_event):
        """Получить подсказки автодополнения."""
        word = document.get_word_before_cursor()

        if word.startswith("/"):
            # Автодополнение команд
            for cmd in self.commands:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))

        elif word.startswith("@"):
            # Автодополнение навыков
            for skill in self.skills:
                if skill.startswith(word[1:]):
                    yield Completion("@" + skill, start_position=-len(word))

        elif word.startswith("$"):
            # Автодополнение моделей
            for model in self.models:
                if model.startswith(word[1:]):
                    yield Completion("$" + model, start_position=-len(word))


class InputHandler:
    """Обработчик пользовательского ввода."""

    def __init__(
        self,
        history_file: str = ".assistant_history",
        commands: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
    ):
        """
        Инициализация.

        Args:
            history_file: Файл истории
            commands: Список команд
            skills: Список навыков
            models: Список моделей
        """
        self.history_file = history_file
        self.theme = get_theme_manager()

        # Создаем историю
        self.history = FileHistory(history_file)

        # Создаем автодополнитель
        self.completer = CommandCompleter(
            commands or [],
            skills or [],
            models or [],
        )

        # Создаем сессию ввода
        self.session = PromptSession(
            history=self.history,
            completer=self.completer,
            enable_history_search=True,
            mouse_support=True,
        )

        logger.info("⌨️ InputHandler инициализирован")

    async def get_input(
        self,
        prompt: str = "👤 Вы: ",
        multiline: bool = False,
    ) -> Optional[str]:
        """
        Получить ввод пользователя.

        Args:
            prompt: Приглашение
            multiline: Многострочный ввод

        Returns:
            Введенный текст
        """
        try:
            # Форматируем приглашение
            # from rich.text import Text

            # prompt_text = Text(prompt, style=self.theme.current_theme.primary)

            # Получаем ввод
            user_input = await self.session.prompt_async(
                prompt,
                multiline=multiline,
            )

            return user_input.strip() if user_input else None

        except (KeyboardInterrupt, EOFError):
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка ввода: {e}")
            return None

    def update_completions(
        self,
        commands: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
    ) -> None:
        """
        Обновить список автодополнений.

        Args:
            commands: Список команд
            skills: Список навыков
            models: Список моделей
        """
        if commands:
            self.completer.commands = commands
        if skills:
            self.completer.skills = skills
        if models:
            self.completer.models = models

    def clear_history(self) -> None:
        """Очистить историю."""
        try:
            Path(self.history_file).unlink(missing_ok=True)
            logger.info("🗑️ История очищена")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки истории: {e}")

    def export_history(self, output_file: str) -> None:
        """
        Экспортировать историю.

        Args:
            output_file: Файл для экспорта
        """
        try:
            with open(self.history_file, "r") as f:
                history_content = f.read()

            with open(output_file, "w") as f:
                f.write(history_content)

            logger.info(f"✅ История экспортирована в {output_file}")

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта истории: {e}")

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"InputHandler(history_file={self.history_file})"