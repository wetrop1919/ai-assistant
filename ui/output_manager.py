"""
Управление выводом с пагинацией, сохранением и фильтрацией.
"""

import logging
from typing import List, Optional
from pathlib import Path
import subprocess

from rich.console import Console
from rich.pager import Pager

logger = logging.getLogger(__name__)


class OutputManager:
    """Менеджер вывода."""

    def __init__(self, console: Console, page_size: int = 20):
        """
        Инициализация.

        Args:
            console: Rich консоль
            page_size: Размер страницы для пагинации
        """
        self.console = console
        self.page_size = page_size
        self.last_output: Optional[str] = None
        self.output_buffer: List[str] = []

    def print(self, content: str, paginate: bool = False) -> None:
        """
        Вывести содержимое.

        Args:
            content: Содержимое
            paginate: Использовать пагинацию
        """
        self.last_output = content
        self.output_buffer.append(content)

        if paginate and len(content.split("\n")) > self.page_size:
            self._paginate(content)
        else:
            self.console.print(content)

    def _paginate(self, content: str) -> None:
        """Вывести с пагинацией."""
        lines = content.split("\n")
        for i in range(0, len(lines), self.page_size):
            page = "\n".join(lines[i:i + self.page_size])
            self.console.print(page)

            if i + self.page_size < len(lines):
                input("\n[нажмите Enter для следующей страницы]")

    def save_output(self, filename: str) -> bool:
        """
        Сохранить последний вывод в файл.

        Args:
            filename: Имя файла

        Returns:
            True если успешно
        """
        try:
            if not self.last_output:
                logger.warning("⚠️ Нет вывода для сохранения")
                return False

            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.last_output)

            logger.info(f"✅ Вывод сохранен в {filename}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
            return False

    def copy_last_output(self) -> bool:
        """
        Скопировать последний вывод в буфер обмена.

        Returns:
            True если успешно
        """
        try:
            if not self.last_output:
                logger.warning("⚠️ Нет вывода для копирования")
                return False

            import pyperclip

            pyperclip.copy(self.last_output)
            logger.info("✅ Вывод скопирован в буфер обмена")
            return True

        except ImportError:
            logger.warning("⚠️ pyperclip не установлен")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка копирования: {e}")
            return False

    def filter_output(self, pattern: str) -> str:
        """
        Отфильтровать вывод (grep).

        Args:
            pattern: Шаблон для поиска

        Returns:
            Отфильтрованный вывод
        """
        try:
            if not self.last_output:
                return ""

            filtered = "\n".join([
                line for line in self.last_output.split("\n")
                if pattern.lower() in line.lower()
            ])

            return filtered

        except Exception as e:
            logger.error(f"❌ Ошибка фильтрации: {e}")
            return self.last_output

    def clear_buffer(self) -> None:
        """Очистить буфер вывода."""
        self.output_buffer.clear()
        self.last_output = None

    def get_buffer_summary(self) -> str:
        """Получить краткую информацию о буфере."""
        return f"📊 Буфер: {len(self.output_buffer)} записей, последний вывод: {len(self.last_output or '')} символов"

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"OutputManager(buffer_size={len(self.output_buffer)})"