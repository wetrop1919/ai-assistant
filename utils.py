"""
Утилиты для приложения: ASCII арт, прогресс-бар, и вспомогательные функции.
"""

import sys
from typing import Optional, Callable, Any
from tqdm import tqdm
import time


class AsciiArt:
    """ASCII арт для приложения."""

    BANNER = r"""
    ╔═════════════════════════════════════════════════════════════╗
    ║                                                             ║
    ║            🤖  AI ASSISTANT v0.1.5  🤖                      ║
    ║                                                             ║
    ║         Personal AI Assistant with Voice & Memory           ║
    ║                                                             ║
    ║      Powered by Llama 3 | Faster-Whisper | pyttsx3          ║
    ║                                                             ║
    ╚═════════════════════════════════════════════════════════════╝
    """

    LOADING = r"""
    ⠋ Инициализация...
    ⠙ Загрузка моделей...
    ⠹ Подключение к Ollama...
    ⠸ Готово!
    """

    WAVE = r"""
    ▁ ▂ ▃ ▄ ▅ ▆ ▇ █ ▇ ▆ ▅ ▄ ▃ ▂ ▁
    """

    SEPARATOR = "─" * 60

    @staticmethod
    def print_banner() -> None:
        """Вывести баннер приложения."""
        print(AsciiArt.BANNER)

    @staticmethod
    def print_separator() -> None:
        """Вывести разделитель."""
        print(AsciiArt.SEPARATOR)

    @staticmethod
    def print_listening() -> None:
        """Вывести статус 'слушаю'."""
        print("\n🎤 Слушаю...")

    @staticmethod
    def print_thinking() -> None:
        """Вывести статус 'думаю'."""
        print("🧠 Думаю...")

    @staticmethod
    def print_speaking() -> None:
        """Вывести статус 'говорю'."""
        print("🔊 Говорю...")


class ProgressBar:
    """Обёртка над tqdm для красивого прогресс-бара."""

    @staticmethod
    def create_bar(
        iterable,
        desc: str = "Прогресс",
        unit: str = "it",
        color: str = "green",
    ):
        """
        Создать прогресс-бар.

        Args:
            iterable: Итерируемый объект
            desc: Описание
            unit: Единица измерения
            color: Цвет бара

        Returns:
            tqdm объект
        """
        return tqdm(
            iterable,
            desc=desc,
            unit=unit,
            colour=color,
            ascii=False,
        )

    @staticmethod
    def create_bar_manual(
        total: int,
        desc: str = "Прогресс",
        unit: str = "it",
    ):
        """
        Создать ручной прогресс-бар.

        Args:
            total: Всего элементов
            desc: Описание
            unit: Единица измерения

        Returns:
            tqdm объект
        """
        return tqdm(total=total, desc=desc, unit=unit, ascii=False)


class TextFormatter:
    """Форматирование текста."""

    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Форматировать длительность в читаемый вид.

        Args:
            seconds: Секунды

        Returns:
            Отформатированная строка
        """
        if seconds < 60:
            return f"{seconds:.1f}с"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}м"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}ч"

    @staticmethod
    def truncate(text: str, max_length: int = 100) -> str:
        """
        Обрезать текст до максимальной длины.

        Args:
            text: Текст
            max_length: Максимальная длина

        Returns:
            Обрезанный текст
        """
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    @staticmethod
    def format_box(text: str, width: int = 60) -> str:
        """
        Форматировать текст в рамку.

        Args:
            text: Текст
            width: Ширина рамки

        Returns:
            Текст в рамке
        """
        lines = text.split("\n")
        boxed = [
            "┌" + "─" * (width - 2) + "┐",
        ]
        for line in lines:
            padded = line.ljust(width - 2)
            boxed.append("│ " + padded + " │")
        boxed.append("└" + "─" * (width - 2) + "┘")
        return "\n".join(boxed)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> Callable:
    """
    Декоратор для повторной попытки при ошибке.

    Args:
        max_attempts: Максимум попыток
        delay: Задержка в секундах
        backoff: Множитель задержки

    Returns:
        Декоратор
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    print(
                        f"❌ Ошибка: {e}. "
                        f"Повтор через {current_delay:.1f}с... "
                        f"({attempt}/{max_attempts})"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        return wrapper
    return decorator
