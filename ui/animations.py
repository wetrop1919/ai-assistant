"""
Анимации загрузки и индикаторы прогресса.
"""

import logging
import asyncio
from typing import Optional, AsyncGenerator
import itertools

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.live import Live
from rich.text import Text

logger = logging.getLogger(__name__)


class AnimationManager:
    """Менеджер анимаций."""

    # Спиннеры
    SPINNERS = [
        "dots",
        "dots2",
        "dots3",
        "dots4",
        "dots5",
        "dots6",
        "dots7",
        "dots8",
        "dots9",
        "dots10",
        "dots11",
        "line",
        "line2",
        "pipe",
        "simpleDots",
        "simpleDotsScrolling",
        "star",
        "star2",
        "flip",
        "hamburger",
        "growVertical",
        "growHorizontal",
        "balloon",
        "balloon2",
        "noise",
        "bounce",
        "boxBounce",
        "boxBounce2",
        "triangle",
        "arc",
        "circle",
        "squareCorners",
        "circleQuarters",
        "circleHalves",
        "squish",
        "toggle",
        "toggle2",
        "toggle3",
        "toggle4",
        "toggle5",
        "toggle6",
        "toggle7",
        "toggle8",
        "toggle9",
        "toggle10",
        "toggle11",
        "toggle12",
        "toggle13",
        "arrow",
        "arrow2",
        "arrow3",
        "bouncingBar",
        "bouncingBall",
        "smiley",
        "monkey",
        "hearts",
        "clock",
        "earth",
        "moon",
        "runner",
        "pong",
        "shark",
        "dqpb",
        "weather",
        "christmas",
        "grenade",
        "point",
        "layer",
    ]

    def __init__(self, console: Optional[Console] = None):
        """
        Инициализация.

        Args:
            console: Rich консоль
        """
        self.console = console or Console()
        self._spinner_index = 0

    async def thinking(self, duration: Optional[float] = None) -> AsyncGenerator[str, None]:
        """
        Анимация "думаю".

        Args:
            duration: Длительность в секундах

        Yields:
            Текущий спиннер
        """
        spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        start = asyncio.get_event_loop().time()

        while True:
            if duration and asyncio.get_event_loop().time() - start > duration:
                break

            for char in spinner_chars:
                yield f"🤔 Думаю {char}"
                await asyncio.sleep(0.1)

    async def loading(self, task: str, duration: Optional[float] = None) -> AsyncGenerator[str, None]:
        """
        Анимация загрузки.

        Args:
            task: Описание задачи
            duration: Длительность

        Yields:
            Текущая строка прогресса
        """
        start = asyncio.get_event_loop().time()

        while True:
            if duration and asyncio.get_event_loop().time() - start > duration:
                break

            for i in range(101):
                percent = i % 101
                bar = "█" * (percent // 5) + "░" * (20 - percent // 5)
                yield f"⏳ {task}: [{bar}] {percent}%"
                await asyncio.sleep(0.05)

    async def voice_input(self) -> AsyncGenerator[str, None]:
        """
        Анимация голосового ввода.

        Yields:
            Текущая анимация
        """
        chars = "🔴🔵🟢🟡"
        index = 0

        for _ in range(100):
            yield f"{chars[index]} Слушаю..."
            index = (index + 1) % len(chars)
            await asyncio.sleep(0.2)

    async def file_progress(
        self,
        current: int,
        total: int,
        filename: str = "",
    ) -> str:
        """
        Прогресс файловой операции.

        Args:
            current: Текущее значение
            total: Общее значение
            filename: Имя файла

        Returns:
            Строка прогресса
        """
        percent = (current / total * 100) if total > 0 else 0
        filled = int(percent / 5)
        bar = "█" * filled + "░" * (20 - filled)

        return f"📁 {filename}: [{bar}] {percent:.1f}% ({current}/{total})"

    def typing_effect(self, text: str, speed: float = 0.02) -> AsyncGenerator[str, None]:
        """
        Эффект печатающегося текста.

        Args:
            text: Текст
            speed: Скорость печати

        Yields:
            Частично печатанный текст
        """
        async def _typing():
            for i in range(len(text) + 1):
                yield text[:i]
                await asyncio.sleep(speed)

        return _typing()

    async def show_progress_with_live(
        self,
        description: str,
        task_func,
        total: int = 100,
    ):
        """
        Показать прогресс с Live обновлением.

        Args:
            description: Описание
            task_func: Асинхронная функция
            total: Общее значение
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
        ) as progress:
            task_id = progress.add_task(description, total=total)

            for i in range(total):
                await task_func(i)
                progress.update(task_id, advance=1)
                await asyncio.sleep(0.01)

    def __repr__(self) -> str:
        """Строковое представление."""
        return "AnimationManager()"


# Глобальный менеджер анимаций
_animation_manager = AnimationManager()


def get_animation_manager() -> AnimationManager:
    """Получить менеджер анимаций."""
    return _animation_manager