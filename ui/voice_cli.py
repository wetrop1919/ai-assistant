"""
Голосовой интерфейс для AI Assistant.
"""

import logging
import asyncio
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from config import config

logger = logging.getLogger(__name__)
console = Console()


class VoiceCLI:
    """Голосовой интерфейс."""

    def __init__(self, brain, memory):
        """
        Инициализация.

        Args:
            brain: Мозг ассистента
            memory: Система памяти
        """
        self.brain = brain
        self.memory = memory
        self.is_running = False

    async def show_welcome(self) -> None:
        """Показать приветствие."""
        console.print("\n[bold cyan]🎤 Голосовой режим активирован[/bold cyan]")
        console.print("[yellow]Говорите активное слово: ассистент[/yellow]")
        console.print("[dim]Или нажмите Ctrl+C для выхода[/dim]\n")

    async def listen_for_wake_word(self) -> bool:
        """
        Слушать слово активации.

        Returns:
            True если услышано
        """
        console.print("👂 Жду слова активации...")

        # Ждем активного слова
        success, text = await self.brain.voice_system.listen_and_transcribe(
            silence_duration=1.0
        )

        if success:
            # Проверяем наличие активного слова
            text_lower = text.lower()
            for wake_word in config.speech.wake_words:
                if wake_word in text_lower:
                    console.print(f"✅ Услышано: '{wake_word}'")
                    return True

        return False

    async def process_voice_input(self) -> None:
        """Обработать голосовой ввод."""
        console.print("🎤 Слушаю команду...")

        success, text = await self.brain.voice_system.listen_and_transcribe()

        if not success:
            console.print(f"[red]{text}[/red]")
            return

        console.print(f"[cyan]Вы сказали:[/cyan] {text}\n")

        # Добавляем в память
        if self.memory:
            self.memory.add_episodic_memory(
                event_type="voice_input",
                content=text,
                importance=0.7,
            )

        # Показываем спиннер
        with Live(Spinner("dots", text="Думаю..."), refresh_per_second=12.5):
            # Генерируем ответ
            try:
                answer = await self.brain.generate(prompt=text)

                # Сохраняем в память
                if self.memory:
                    self.memory.add_episodic_memory(
                        event_type="assistant_response",
                        content=answer,
                        importance=0.7,
                    )

                # Выводим ответ
                console.print(f"\n[green]Ассистент:[/green] {answer}\n")

                # Произносим ответ
                self.brain.speak_response(answer, wait=False)

            except Exception as e:
                logger.error(f"❌ Ошибка обработки: {e}")
                console.print(f"[red]❌ Ошибка: {e}[/red]\n")

    async def run(self) -> None:
        """Запустить голосовой интерфейс."""
        self.is_running = True

        try:
            await self.show_welcome()

            while self.is_running:
                try:
                    # Ждем активного слова
                    if await self.listen_for_wake_word():
                        # Обрабатываем команду
                        await self.process_voice_input()
                    else:
                        # Продолжаем слушать
                        await asyncio.sleep(0.1)

                except KeyboardInterrupt:
                    console.print("\n[yellow]👋 Выход из голосового режима[/yellow]")
                    break
                except Exception as e:
                    logger.error(f"❌ Ошибка: {e}")
                    console.print(f"[red]❌ Ошибка: {e}[/red]")

        finally:
            self.is_running = False

    def __repr__(self) -> str:
        """Строковое представление."""
        return "VoiceCLI()"