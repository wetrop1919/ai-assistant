"""
Форматтеры для красивого вывода через Rich.
"""

import logging
from typing import List, Dict, Any, Optional
from io import StringIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.align import Align
from rich.text import Text
from rich import box

from .themes import get_theme_manager

logger = logging.getLogger(__name__)

# Глобальная консоль
console = Console()


class Formatter:
    """Базовый форматтер."""

    def __init__(self):
        """Инициализация."""
        self.theme = get_theme_manager()

    def format_code(
        self,
        code: str,
        language: str = "python",
        line_numbers: bool = True,
    ) -> str:
        """
        Форматировать код с подсветкой синтаксиса.

        Args:
            code: Исходный код
            language: Язык программирования
            line_numbers: Показывать номера строк

        Returns:
            Форматированный код
        """
        try:
            syntax = Syntax(
                code,
                language,
                theme="monokai",
                line_numbers=line_numbers,
                word_wrap=True,
                background_color="black",
            )
            return syntax
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования кода: {e}")
            return code

    def format_table(
        self,
        data: List[Dict[str, Any]],
        title: Optional[str] = None,
    ) -> Table:
        """
        Форматировать таблицу.

        Args:
            data: Данные таблицы
            title: Заголовок

        Returns:
            Таблица Rich
        """
        try:
            if not data:
                return Table(title=title or "Таблица", box=box.ROUNDED)

            # Создаем таблицу
            table = Table(
                title=title,
                box=box.ROUNDED,
                header_style=self.theme.current_theme.header_style,
            )

            # Добавляем колонки
            columns = list(data[0].keys())
            for column in columns:
                table.add_column(column, style=self.theme.current_theme.primary)

            # Добавляем строки
            for row in data:
                table.add_row(*[str(row.get(col, "")) for col in columns])

            return table

        except Exception as e:
            logger.error(f"❌ Ошибка форматирования таблицы: {e}")
            return Table(title=title or "Таблица")

    def format_list(
        self,
        items: List[str],
        style: str = "bullet",
        title: Optional[str] = None,
    ) -> str:
        """
        Форматировать список.

        Args:
            items: Элементы списка
            style: Стиль (bullet, number, dash)
            title: Заголовок

        Returns:
            Форматированный список
        """
        if not items:
            return ""

        try:
            if style == "bullet":
                prefix = "• "
            elif style == "number":
                prefix = "1. "
            elif style == "dash":
                prefix = "- "
            else:
                prefix = "• "

            formatted = "\n".join([f"{prefix}{item}" for item in items])

            if title:
                formatted = f"[bold]{title}[/bold]\n{formatted}"

            return formatted

        except Exception as e:
            logger.error(f"❌ Ошибка форматирования списка: {e}")
            return "\n".join(items)

    def format_panel(
        self,
        content: str,
        title: str = "",
        style: str = "info",
        width: Optional[int] = None,
    ) -> Panel:
        """
        Форматировать панель.

        Args:
            content: Содержимое
            title: Заголовок
            style: Стиль (info, success, error, warning)
            width: Ширина

        Returns:
            Панель Rich
        """
        try:
            color_map = {
                "info": self.theme.current_theme.primary,
                "success": self.theme.current_theme.success,
                "error": self.theme.current_theme.error,
                "warning": self.theme.current_theme.warning,
            }

            color = color_map.get(style, self.theme.current_theme.primary)

            panel = Panel(
                content,
                title=title,
                border_style=color,
                width=width,
            )

            return panel

        except Exception as e:
            logger.error(f"❌ Ошибка форматирования панели: {e}")
            return Panel(content, title=title)

    def format_error(self, error: str, title: str = "Ошибка") -> Panel:
        """Форматировать ошибку."""
        emoji = self.theme.current_theme.emoji_error
        return self.format_panel(
            f"{emoji} {error}",
            title=title,
            style="error",
        )

    def format_success(self, message: str, title: str = "Успех") -> Panel:
        """Форматировать успех."""
        emoji = self.theme.current_theme.emoji_success
        return self.format_panel(
            f"{emoji} {message}",
            title=title,
            style="success",
        )

    def format_warning(self, message: str, title: str = "Предупреждение") -> Panel:
        """Форматировать предупреждение."""
        emoji = self.theme.current_theme.emoji_warning
        return self.format_panel(
            f"{emoji} {message}",
            title=title,
            style="warning",
        )

    def format_info(self, message: str, title: str = "Информация") -> Panel:
        """Форматировать информацию."""
        emoji = self.theme.current_theme.emoji_info
        return self.format_panel(
            f"{emoji} {message}",
            title=title,
            style="info",
        )

    def format_status(self, component: str, status: str) -> str:
        """
        Форматировать статус компонента.

        Args:
            component: Имя компонента
            status: Статус (available, unavailable, degraded)

        Returns:
            Форматированный статус
        """
        emoji_map = {
            "available": "🟢",
            "unavailable": "🔴",
            "degraded": "🟡",
            "unknown": "⚪",
        }

        emoji = emoji_map.get(status, "⚪")
        return f"{emoji} {component}: {status}"

    def format_markdown(self, markdown_text: str) -> Markdown:
        """Форматировать Markdown."""
        return Markdown(markdown_text)

    def print_output(self, content: Any, **kwargs) -> None:
        """Вывести содержимое."""
        console.print(content, **kwargs)

    def print_error(self, error: str) -> None:
        """Вывести ошибку."""
        self.print_output(self.format_error(error))

    def print_success(self, message: str) -> None:
        """Вывести успех."""
        self.print_output(self.format_success(message))

    def print_warning(self, message: str) -> None:
        """Вывести предупреждение."""
        self.print_output(self.format_warning(message))

    def print_info(self, message: str) -> None:
        """Вывести информацию."""
        self.print_output(self.format_info(message))

    def print_table(self, data: List[Dict[str, Any]], title: str = "") -> None:
        """Вывести таблицу."""
        self.print_output(self.format_table(data, title=title))

    def print_code(self, code: str, language: str = "python") -> None:
        """Вывести код."""
        self.print_output(self.format_code(code, language))


# Глобальный форматтер
_formatter = Formatter()


def get_formatter() -> Formatter:
    """Получить глобальный форматтер."""
    return _formatter