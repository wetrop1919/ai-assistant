"""
Полная система голоса и голосового ввода.

Включает:
- Speech-to-Text (Whisper)
- Text-to-Speech (pyttsx3)
- Детектор активности речи (VAD)
- Обработка аудиопотока
"""

import logging
import asyncio
import numpy as np
from typing import Optional, Callable, Tuple
from pathlib import Path
import wave
import struct
from enum import Enum

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Формат аудио."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


class VoiceActivityDetector:
    """Детектор активности речи (Voice Activity Detection)."""

    def __init__(self, sensitivity: int = 2):
        """
        Инициализация.

        Args:
            sensitivity: Чувствительность (1-3)
        """
        try:
            import webrtcvad

            self.vad = webrtcvad.Vad(sensitivity)
            self.is_available = True
            logger.info(f"✅ VAD инициализирован (sensitivity={sensitivity})")

        except ImportError:
            logger.warning("⚠️ webrtcvad не установлен")
            self.vad = None
            self.is_available = False

    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """
        Проверить содержит ли аудиочанк речь.

        Args:
            audio_chunk: Аудиоданные
            sample_rate: Частота дискретизации

        Returns:
            True если содержит речь
        """
        if not self.is_available or not self.vad:
            return True  # Если VAD недоступен, считаем что это речь

        try:
            return self.vad.is_speech(audio_chunk, sample_rate)
        except Exception as e:
            logger.warning(f"⚠️ Ошибка VAD: {e}")
            return True


class AudioRecorder:
    """Записывающее устройство для аудио."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 2048,
        device_index: Optional[int] = None,
    ):
        """
        Инициализация.

        Args:
            sample_rate: Частота дискретизации
            chunk_size: Размер буфера
            device_index: Индекс аудиоустройства
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.is_recording = False
        self.audio_data: np.ndarray = np.array([], dtype=np.float32)

        try:
            import sounddevice as sd

            self.sd = sd
            logger.info("✅ SoundDevice инициализирован")

        except ImportError:
            logger.warning("⚠️ sounddevice не установлен")
            self.sd = None

    async def record_until_silence(
        self,
        silence_duration: float = 2.0,
        max_duration: float = 30.0,
        on_chunk: Optional[Callable] = None,
    ) -> np.ndarray:
        """
        Записать аудио до тишины.

        Args:
            silence_duration: Длительность тишины для остановки (сек)
            max_duration: Максимальная длительность записи (сек)
            on_chunk: Callback для каждого чанка

        Returns:
            Аудиоданные
        """
        if not self.sd:
            logger.error("❌ SoundDevice не доступен")
            return np.array([], dtype=np.float32)

        try:
            self.is_recording = True
            logger.info("🎤 Начинаю запись...")

            vad = VoiceActivityDetector()
            audio_chunks = []
            silence_chunks = 0
            max_chunks = int(max_duration * self.sample_rate / self.chunk_size)
            silence_threshold = int(silence_duration * self.sample_rate / self.chunk_size)

            # Записываем аудио
            with self.sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                blocksize=self.chunk_size,
                device=self.device_index,
            ) as stream:

                while self.is_recording:
                    # Читаем данные
                    chunk, overflowed = stream.read(self.chunk_size)

                    if overflowed:
                        logger.warning("⚠️ Переполнение аудиобуфера")

                    # Конвертируем в bytes для VAD
                    chunk_bytes = (chunk * 32767).astype(np.int16).tobytes()

                    # Проверяем наличие речи
                    has_speech = vad.is_speech(chunk_bytes, self.sample_rate)

                    if has_speech:
                        silence_chunks = 0
                        audio_chunks.append(chunk)
                        logger.debug("🔊 Речь обнаружена")

                    else:
                        silence_chunks += 1
                        audio_chunks.append(chunk)
                        logger.debug(f"🔇 Тишина: {silence_chunks}/{silence_threshold}")

                    # Callback
                    if on_chunk:
                        if asyncio.iscoroutinefunction(on_chunk):
                            await on_chunk(chunk)
                        else:
                            on_chunk(chunk)

                    # Условия остановки
                    if silence_chunks > silence_threshold and len(audio_chunks) > 10:
                        logger.info("⏹️ Обнаружена тишина, завершаю запись")
                        break

                    if len(audio_chunks) > max_chunks:
                        logger.warning("⏹️ Достигнута максимальная длительность")
                        break

                    await asyncio.sleep(0.01)

            # Объединяем чанки
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks)
                logger.info(f"✅ Запись завершена ({len(audio_data) / self.sample_rate:.1f}с)")
                return audio_data

            return np.array([], dtype=np.float32)

        except Exception as e:
            logger.error(f"❌ Ошибка записи: {e}")
            return np.array([], dtype=np.float32)

        finally:
            self.is_recording = False

    def save_audio(self, audio_data: np.ndarray, filepath: str) -> bool:
        """
        Сохранить аудио в файл.

        Args:
            audio_data: Аудиоданные
            filepath: Путь к файлу

        Returns:
            True если успешно
        """
        try:
            import soundfile as sf

            sf.write(filepath, audio_data, self.sample_rate)
            logger.info(f"✅ Аудио сохранено: {filepath}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
            return False

    def stop_recording(self) -> None:
        """Остановить запись."""
        self.is_recording = False
        logger.info("⏹️ Запись остановлена")


class SpeechToText:
    """Преобразование речи в текст (Speech-to-Text)."""

    def __init__(self, model: str = "base", language: str = "ru"):
        """
        Инициализация.

        Args:
            model: Размер модели (tiny, base, small, medium, large)
            language: Язык
        """
        self.model_name = model
        self.language = language
        self.model = None

        try:
            from faster_whisper import WhisperModel

            logger.info(f"📥 Загружаю Whisper модель {model}...")
            self.model = WhisperModel(model, device="auto", compute_type="auto")
            logger.info(f"✅ Whisper инициализирована")

        except ImportError:
            logger.error("❌ faster-whisper не установлена")

    async def transcribe(self, audio_path: str) -> Tuple[bool, str]:
        """
        Транскрибировать аудиофайл.

        Args:
            audio_path: Путь к аудиофайлу

        Returns:
            Кортеж (успех, текст)
        """
        if not self.model:
            return False, "❌ Whisper не инициализирована"

        try:
            logger.info(f"🎧 Транскрибирую: {audio_path}")

            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
                beam_size=5,
                best_of=5,
            )

            # Объединяем сегменты
            text = " ".join(segment.text for segment in segments)

            logger.info(f"✅ Транскрибировано: {len(text)} символов")
            return True, text

        except Exception as e:
            logger.error(f"❌ Ошибка транскрибирования: {e}")
            return False, f"❌ Ошибка: {e}"

    async def transcribe_audio_data(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> Tuple[bool, str]:
        """
        Транскрибировать аудиоданные напрямую.

        Args:
            audio_data: Аудиоданные
            sample_rate: Частота дискретизации

        Returns:
            Кортеж (успех, текст)
        """
        if not self.model:
            return False, "❌ Whisper не инициализирована"

        try:
            import tempfile
            import soundfile as sf

            # Сохраняем временно
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio_data, sample_rate)
                temp_path = tmp.name

            # Транскрибируем
            success, text = await self.transcribe(temp_path)

            # Удаляем временный файл
            Path(temp_path).unlink(missing_ok=True)

            return success, text

        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False, f"❌ Ошибка: {e}"


class TextToSpeech:
    """Преобразование текста в речь (Text-to-Speech)."""

    def __init__(
        self,
        engine: str = "pyttsx3",
        language: str = "ru",
        rate: int = 150,
        volume: float = 1.0,
    ):
        """
        Инициализация.

        Args:
            engine: Движок TTS (pyttsx3, gtts)
            language: Язык
            rate: Скорость речи
            volume: Громкость (0.0-1.0)
        """
        self.engine_name = engine
        self.language = language
        self.rate = rate
        self.volume = volume
        self.engine = None

        if engine == "pyttsx3":
            self._init_pyttsx3()

    def _init_pyttsx3(self) -> None:
        """Инициализировать pyttsx3."""
        try:
            import pyttsx3

            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.rate)
            self.engine.setProperty("volume", self.volume)

            # Устанавливаем русский голос если возможно
            voices = self.engine.getProperty("voices")
            for voice in voices:
                if "russian" in voice.name.lower() or "ru" in voice.id.lower():
                    self.engine.setProperty("voice", voice.id)
                    break

            logger.info("✅ pyttsx3 инициализирована")

        except ImportError:
            logger.error("❌ pyttsx3 не установлена")

    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Произнести текст.

        Args:
            text: Текст для произнесения
            wait: Ждать завершения

        Returns:
            True если успешно
        """
        if not self.engine:
            logger.error("❌ TTS не инициализирована")
            return False

        try:
            logger.info(f"🔊 Произношу: {text[:50]}...")
            self.engine.say(text)

            if wait:
                self.engine.runAndWait()

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка произнесения: {e}")
            return False

    def save_to_file(self, text: str, filepath: str) -> bool:
        """
        Сохранить речь в файл.

        Args:
            text: Текст
            filepath: Путь к файлу

        Returns:
            True если успешно
        """
        if not self.engine:
            return False

        try:
            self.engine.save_to_file(text, filepath)
            self.engine.runAndWait()
            logger.info(f"✅ Аудио сохранено: {filepath}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
            return False


class VoiceSystem:
    """Полная система голоса."""

    def __init__(
        self,
        tts_engine: str = "pyttsx3",
        stt_model: str = "base",
        language: str = "ru",
    ):
        """
        Инициализация.

        Args:
            tts_engine: Движок TTS
            stt_model: Модель STT
            language: Язык
        """
        self.language = language
        self.tts = TextToSpeech(engine=tts_engine, language=language)
        self.stt = SpeechToText(model=stt_model, language=language)
        self.recorder = AudioRecorder()

        logger.info("🎤 VoiceSystem инициализирована")

    async def listen_and_transcribe(
        self,
        silence_duration: float = 2.0,
        show_progress: bool = True,
    ) -> Tuple[bool, str]:
        """
        Слушать и транскрибировать речь.

        Args:
            silence_duration: Длительность тишины для остановки
            show_progress: Показывать прогресс

        Returns:
            Кортеж (успех, текст)
        """
        try:
            if show_progress:
                from rich.console import Console
                console = Console()
                console.print("🎤 Слушаю... (говорите)")

            # Записываем аудио
            audio_data = await self.recorder.record_until_silence(
                silence_duration=silence_duration
            )

            if len(audio_data) == 0:
                logger.warning("⚠️ Не удалось записать аудио")
                return False, "❌ Не удалось записать аудио"

            # Транскрибируем
            success, text = await self.stt.transcribe_audio_data(audio_data)

            if success:
                logger.info(f"📝 Услышал: {text}")
                return True, text

            return False, text

        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return False, f"❌ Ошибка: {e}"

    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Произнести текст.

        Args:
            text: Текст
            wait: Ждать завершения

        Returns:
            True если успешно
        """
        return self.tts.speak(text, wait=wait)

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"VoiceSystem("
            f"tts={self.tts.engine_name}, "
            f"stt={self.stt.model_name}, "
            f"language={self.language})"
        )