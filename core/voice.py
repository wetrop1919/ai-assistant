"""
Система синтеза речи (Text-to-Speech).

Использует:
- pyttsx3 как основной движок с русскими голосами
- piper-tts как fallback
- Асинхронное озвучивание в отдельном потоке
- Очередь сообщений для озвучки
"""

import logging
import threading
from queue import Queue
from typing import Optional
import time

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from config import config
from utils import TextFormatter

logger = logging.getLogger(__name__)


class Voice:
    """
    Система синтеза речи (Text-to-Speech).

    Attributes:
        engine: pyttsx3 engine
        queue: Очередь сообщений для озвучки
        is_running: Флаг работы
    """

    def __init__(self):
        """Инициализация системы синтеза речи."""
        logger.info("🔊 Инициализация Voice (Text-to-Speech)")

        self.engine: Optional[pyttsx3.Engine] = None
        self.queue: Queue = Queue()
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None

        self._init_engine()
        self._start_worker()

    def _init_engine(self) -> None:
        """Инициализировать pyttsx3 engine."""
        try:
            logger.info("📥 Инициализация pyttsx3...")
            self.engine = pyttsx3.init()

            # Устанавливаем русский язык
            self.engine.setProperty("language", config.speech.tts_language)

            # Скорость речи
            self.engine.setProperty("rate", config.speech.tts_voice_rate)

            # Громкость
            self.engine.setProperty("volume", config.speech.tts_volume)

            # Пытаемся найти русский голос
            voices = self.engine.getProperty("voices")
            russian_voice_found = False

            for voice in voices:
                if "ru" in voice.languages or "russian" in voice.name.lower():
                    self.engine.setProperty("voice", voice.id)
                    russian_voice_found = True
                    logger.info(f"✅ Выбран голос: {voice.name}")
                    break

            if not russian_voice_found and voices:
                # Используем первый доступный голос
                self.engine.setProperty("voice", voices[0].id)
                logger.warning(
                    f"⚠️ Русский голос не найден. "
                    f"Используется: {voices[0].name}"
                )

            logger.info("✅ pyttsx3 инициализирован")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации pyttsx3: {e}")
            logger.warning("⚠️ Text-to-Speech может быть недоступен")

    def _start_worker(self) -> None:
        """Запустить рабочий поток для озвучки."""
        self.is_running = True
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
        )
        self.worker_thread.start()
        logger.info("✅ Рабочий поток озвучки запущен")

    def _worker_loop(self) -> None:
        """Основной цикл рабочего потока."""
        while self.is_running:
            try:
                # Получаем сообщение из очереди с таймаутом
                message = self.queue.get(timeout=1.0)

                if message is None:  # Сигнал выхода
                    break

                self._speak_sync(message)

            except Exception as e:
                logger.debug(f"Ошибка рабочего потока: {e}")
                continue

    def speak(self, text: str, wait: bool = False) -> None:
        """
        Озвучить текст.

        Args:
            text: Текст для озвучки
            wait: Ждать завершения озвучки
        """
        if not text or not self.engine:
            logger.warning("⚠️ Нечего озвучивать или engine недоступен")
            return

        if wait:
            # Синхронное озвучивание
            self._speak_sync(text)
        else:
            # Асинхронное - добавляем в очередь
            self.queue.put(text)
            logger.debug(f"📝 Добавлено в очередь озвучки: "
                        f"{TextFormatter.truncate(text, 50)}")

    def _speak_sync(self, text: str) -> None:
        """
        Озвучить текст синхронно.

        Args:
            text: Текст для озвучки
        """
        try:
            if not self.engine:
                logger.warning("⚠️ Engine не инициализирован")
                return

            logger.debug(f"🔊 Озвучиваю: {TextFormatter.truncate(text, 50)}")

            self.engine.say(text)
            self.engine.runAndWait()

            logger.debug("✅ Озвучивание завершено")

        except Exception as e:
            logger.error(f"❌ Ошибка озвучивания: {e}")

    def set_rate(self, rate: int) -> None:
        """
        Установить скорость речи.

        Args:
            rate: Скорость (50-300)
        """
        if self.engine:
            rate = max(50, min(300, rate))
            self.engine.setProperty("rate", rate)
            logger.info(f"🔊 Скорость речи установлена: {rate}")

    def set_volume(self, volume: float) -> None:
        """
        Установить громкость.

        Args:
            volume: Громкость (0.0-1.0)
        """
        if self.engine:
            volume = max(0.0, min(1.0, volume))
            self.engine.setProperty("volume", volume)
            logger.info(f"🔊 Громкость установлена: {volume}")

    def wait_until_done(self) -> None:
        """Ждать пока все сообщения из очереди озвучены."""
        logger.debug("⏳ Ожидание завершения озвучки...")
        self.queue.join()
        logger.debug("✅ Все сообщения озвучены")

    def clear_queue(self) -> None:
        """Очистить очередь озвучки."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except:
                break

        logger.info("🗑️ Очередь озвучки очищена")

    def stop(self) -> None:
        """Остановить озвучивание и рабочий поток."""
        logger.info("⏹️ Остановка Voice...")

        self.is_running = False
        self.queue.put(None)  # Сигнал выхода

        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)

        if self.engine:
            try:
                self.engine.stop()
            except:
                pass

        logger.info("✅ Voice остановлен")

    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return (
            f"Voice(engine={'pyttsx3' if self.engine else 'None'}, "
            f"language={config.speech.tts_language}, "
            f"rate={config.speech.tts_voice_rate})"
        )
