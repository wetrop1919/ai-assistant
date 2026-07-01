"""
Система распознавания речи (Speech-to-Text).

Использует:
- faster-whisper с моделью "medium" для русского
- PyAudio для захвата аудио (16kHz, mono)
- webrtcvad для голосовой активации
- Wake word detection "ассистент" и альтернативы
"""

import logging
import threading
from typing import Optional, Callable, List
from pathlib import Path
import tempfile
import numpy as np
import os

logger = logging.getLogger(__name__)

# Опциональные импорты
try:
    import pyaudio
except ImportError:
    pyaudio = None
    logger.warning("⚠️ pyaudio не установлен")

try:
    import webrtcvad
except ImportError:
    webrtcvad = None
    logger.warning("⚠️ webrtcvad не установлен")

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None
    logger.warning("⚠️ faster-whisper не установлен")

from config import config
from utils import retry, ProgressBar


class Ears:
    """
    Система распознавания речи.

    Attributes:
        model: Модель Whisper
        vad: Детектор голосовой активности
        wake_words: Список фраз активации
        is_listening: Флаг активного слушания
    """

    # Параметры аудио
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1024
    AUDIO_FORMAT = 8  # pyaudio.paInt16
    CHANNELS = 1

    def __init__(self):
        """Инициализация системы распознавания речи."""
        logger.info("👂 Инициализация Ears (Speech-to-Text)")

        if WhisperModel is None or pyaudio is None:
            logger.warning("⚠️ Ears недоступны: отсутствуют зависимости")
            self.model = None
            self.vad = None
            self.is_available = False
            return

        self.model: Optional[WhisperModel] = None
        self.vad: Optional[object] = None
        self.wake_words = config.speech.wake_words
        self.wake_word_confidence = config.speech.wake_word_confidence
        self.is_listening = False
        self.is_available = True

        self._audio_stream = None
        self._temp_files = []

        self._load_models()

    def _load_models(self) -> None:
        """Загрузить модели Whisper и VAD с прогресс-баром."""
        try:
            # Подавляем предупреждение HF
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

            # Загрузка модели Whisper
            logger.info(
                f"📥 Загрузка модели Whisper ({config.speech.whisper_model})..."
            )
            logger.info(
                "ℹ️ Первая загрузка может занять время (модель ~500MB)..."
            )

            # Используем кэш для моделей
            model_cache = Path.home() / ".cache" / "whisper"
            model_cache.mkdir(parents=True, exist_ok=True)

            with ProgressBar.create_bar_manual(
                total=100,
                desc="Загрузка Whisper",
            ) as pbar:
                # Добавляем callback для отслеживания прогресса
                def progress_callback(current, total):
                    if total > 0:
                        progress = min(100, int(current * 100 / total))
                        pbar.n = progress
                        pbar.refresh()

                try:
                    self.model = WhisperModel(
                        config.speech.whisper_model,
                        device=config.speech.whisper_device,
                        compute_type="float32",
                        download_root=str(model_cache),
                    )
                except Exception as e:
                    # Fallback если что-то пошло не так
                    logger.warning(f"Загрузка с параметрами не удалась: {e}")
                    self.model = WhisperModel(
                        config.speech.whisper_model,
                        device=config.speech.whisper_device,
                        compute_type="float32",
                    )

                pbar.n = 100
                pbar.refresh()

            logger.info("✅ Модель Whisper загружена")

            # Инициализация VAD (голосовая активация)
            if webrtcvad:
                logger.info("📥 Инициализация VAD...")
                self.vad = webrtcvad.VAD()
                self.vad.set_aggressiveness(1)
                logger.info("✅ VAD инициализирован")
            else:
                logger.warning("⚠️ VAD недоступен (webrtcvad не установлен)")

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки моделей: {e}")
            self.is_available = False

    def _detect_wake_word(self, text: str) -> bool:
        """
        Обнаружить фразу активации в тексте.

        Args:
            text: Распознанный текст

        Returns:
            True если найдена фраза активации
        """
        text_lower = text.lower().strip()

        for wake_word in self.wake_words:
            wake_word_lower = wake_word.lower()
            if wake_word_lower in text_lower:
                logger.info(f"🎤 Фраза активации обнаружена: '{wake_word}'")
                return True

        return False

    @retry(max_attempts=2, delay=2.0)
    def record_audio(
        self,
        duration: float = 5.0,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Optional[str]:
        """
        Записать аудио и распознать речь.

        Args:
            duration: Длительность записи в секундах
            callback: Функция обратного вызова при распознавании

        Returns:
            Распознанный текст
        """
        if not self.is_available:
            logger.warning("⚠️ Ears недоступны")
            return None

        logger.info(f"🎤 Начинаю запись ({duration}с)...")

        try:
            audio_data = self._record_audio_data(duration)

            if audio_data is None or len(audio_data) == 0:
                logger.warning("⚠️ Не удалось записать аудио")
                return None

            # Сохраняем в временный файл
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as tmp_file:
                tmp_path = tmp_file.name
                self._temp_files.append(tmp_path)

                # Простое сохранение WAV
                import wave

                with wave.open(tmp_path, "wb") as wav_file:
                    wav_file.setnchannels(self.CHANNELS)
                    wav_file.setsampwidth(2)  # int16
                    wav_file.setframerate(self.SAMPLE_RATE)
                    wav_file.writeframes(audio_data.tobytes())

            # Распознавание через Whisper
            logger.info("🧠 Распознаю речь...")

            with ProgressBar.create_bar_manual(
                total=100,
                desc="Распознавание",
            ) as pbar:
                segments, info = self.model.transcribe(
                    tmp_path,
                    language=config.speech.whisper_language,
                    beam_size=5,
                    best_of=5,
                )

                text = "".join(segment.text for segment in segments).strip()
                pbar.n = 100
                pbar.refresh()

            if not text:
                logger.warning("⚠️ Не удалось распознать речь")
                return None

            logger.info(f"✅ Распознано: {text}")

            if callback:
                callback(text)

            # Проверка фразы активации
            if self._detect_wake_word(text):
                return text

            return text

        except Exception as e:
            logger.error(f"❌ Ошибка распознавания: {e}")
            return None

    def _record_audio_data(
        self,
        duration: float,
    ) -> Optional[np.ndarray]:
        """
        Записать данные аудио с помощью PyAudio.

        Args:
            duration: Длительность записи

        Returns:
            Массив аудиоданных
        """
        try:
            p = pyaudio.PyAudio()

            stream = p.open(
                format=self.AUDIO_FORMAT,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.CHUNK_SIZE,
            )

            frames = []
            num_frames = int(self.SAMPLE_RATE / self.CHUNK_SIZE * duration)

            logger.debug(f"Запись {num_frames} фреймов...")

            with ProgressBar.create_bar(
                range(num_frames),
                desc="Запись аудио",
                unit="фрейм",
            ) as pbar:
                for _ in pbar:
                    try:
                        data = stream.read(
                            self.CHUNK_SIZE, exception_on_overflow=False
                        )
                        frames.append(np.frombuffer(data, dtype=np.int16))
                    except Exception as e:
                        logger.debug(f"Ошибка чтения фрейма: {e}")
                        continue

            stream.stop_stream()
            stream.close()
            p.terminate()

            audio_data = np.concatenate(frames) if frames else np.array([])
            logger.debug(f"📊 Записано {len(audio_data)} сэмплов")
            return audio_data

        except Exception as e:
            logger.error(f"❌ Ошибка записи аудио: {e}")
            return None

    def listen_continuously(
        self,
        on_heard: Callable[[str], None],
        on_wake_word: Callable[[], None],
    ) -> None:
        """
        Слушать непрерывно в отдельном потоке.

        Args:
            on_heard: Callback при распознавании
            on_wake_word: Callback при обнаружении фразы активации
        """
        if not self.is_available:
            logger.warning("⚠️ Ears недоступны для непрерывного слушания")
            return

        logger.info("🎤 Запущено непрерывное слушание")

        def listen_loop():
            while self.is_listening:
                try:
                    text = self.record_audio(
                        duration=3.0,
                        callback=on_heard,
                    )

                    if text and self._detect_wake_word(text):
                        on_wake_word()

                except KeyboardInterrupt:
                    logger.info("⏹️ Слушание остановлено")
                    break
                except Exception as e:
                    logger.error(f"❌ Ошибка слушания: {e}")

        self.is_listening = True
        thread = threading.Thread(target=listen_loop, daemon=True)
        thread.start()

    def stop_listening(self) -> None:
        """Остановить слушание."""
        self.is_listening = False
        logger.info("⏹️ Слушание остановлено")

    def cleanup(self) -> None:
        """Очистить временные файлы."""
        for tmp_file in self._temp_files:
            try:
                Path(tmp_file).unlink()
            except Exception as e:
                logger.debug(f"Ошибка удаления {tmp_file}: {e}")

        self._temp_files.clear()
        logger.info("🗑️ Временные файлы очищены")

    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return (
            f"Ears(model={config.speech.whisper_model}, "
            f"language={config.speech.whisper_language}, "
            f"available={self.is_available})"
        )