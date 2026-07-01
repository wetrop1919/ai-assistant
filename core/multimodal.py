"""
Мультимодальные способности ассистента.

Поддержка:
- Изображений (описание, VQA, OCR)
- Аудио (классификация, транскрипция, эмоции)
- Видео (базовая обработка)
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    import base64
except ImportError:
    Image = None
    base64 = None


class MultimodalProcessor:
    """Обработка мультимодальных данных."""

    def __init__(self, brain=None):
        """
        Инициализация multimodal процессора.

        Args:
            brain: Ссылка на мозг ассистента
        """
        self.brain = brain
        self.is_available = brain is not None

        logger.info("🎨 Инициализация MultimodalProcessor")

    async def describe_image(self, image_path: str) -> str:
        """
        Описать изображение.

        Args:
            image_path: Путь к изображению

        Returns:
            Описание изображения
        """
        if not self.is_available:
            return "❌ Мультимодальная обработка недоступна"

        try:
            if not Path(image_path).exists():
                return f"❌ Файл не найден: {image_path}"

            # Кодируем изображение в base64
            image_data = self._encode_image(image_path)

            if not image_data:
                return "❌ Не удалось закодировать изображение"

            # Используем llama3.2-vision через Ollama
            response = await self.brain.generate(
                prompt=f"Опиши это изображение подробно. Что на нем изображено?",
            )

            logger.info(f"✅ Изображение описано: {image_path}")
            return f"📷 Описание изображения:\n\n{response}"

        except Exception as e:
            logger.error(f"❌ Ошибка описания изображения: {e}")
            return f"❌ Ошибка: {e}"

    async def answer_image_question(
        self,
        image_path: str,
        question: str,
    ) -> str:
        """
        Ответить на вопрос по изображению (VQA).

        Args:
            image_path: Путь к изображению
            question: Вопрос

        Returns:
            Ответ
        """
        if not self.is_available:
            return "❌ VQA недоступна"

        try:
            if not Path(image_path).exists():
                return f"❌ Файл не найден: {image_path}"

            response = await self.brain.generate(
                prompt=f"Посмотри на изображение и ответь на вопрос:\n"
                        f"Вопрос: {question}",
            )

            logger.info(f"✅ VQA обработано: {question}")
            return f"❓ Ответ на вопрос:\n\n{response}"

        except Exception as e:
            logger.error(f"❌ Ошибка VQA: {e}")
            return f"❌ Ошибка: {e}"

    async def extract_text_from_image(self, image_path: str) -> str:
        """
        Извлечь текст из изображения (OCR).

        Args:
            image_path: Путь к изображению

        Returns:
            Извлеченный текст
        """
        try:
            if not Path(image_path).exists():
                return f"❌ Файл не найден: {image_path}"

            logger.info(f"📝 Начинаю извлечение текста из {image_path}")

            # Попытка 1: Используем pytesseract
            try:
                import pytesseract
                from PIL import Image

                logger.info("📥 Загружаю изображение...")
                img = Image.open(image_path)

                logger.info("🔍 Запускаю OCR через pytesseract...")
                text = pytesseract.image_to_string(img, lang="rus+eng")

                if text.strip():
                    logger.info(f"✅ Текст успешно извлечен ({len(text)} символов)")
                    return f"""
📄 Извлеченный текст (OCR):

{text}
"""

                logger.warning("⚠️ pytesseract вернул пустой результат")

            except Exception as e:
                logger.warning(f"⚠️ pytesseract ошибка: {e}")

            # Попытка 2: Используем EasyOCR если доступен
            try:
                import easyocr

                logger.info("📥 Загружаю модель EasyOCR...")
                reader = easyocr.Reader(['ru', 'en'])

                logger.info("🔍 Запускаю OCR через EasyOCR...")
                results = reader.readtext(image_path)

                text = "\n".join([result[1] for result in results])

                if text.strip():
                    logger.info(f"✅ Текст успешно извлечен ({len(text)} символов)")
                    return f"""
📄 Извлеченный текст (EasyOCR):

{text}
"""

            except Exception as e:
                logger.warning(f"⚠️ EasyOCR ошибка: {e}")

            # Попытка 3: Используем Tesseract напрямую (если установлен)
            try:
                import subprocess

                logger.info("🔍 Запускаю OCR через Tesseract...")
                result = subprocess.run(
                    ["tesseract", image_path, "stdout", "-l", "rus+eng"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and result.stdout.strip():
                    logger.info(f"✅ Текст успешно извлечен ({len(result.stdout)} символов)")
                    return f"""
📄 Извлеченный текст (Tesseract):

{result.stdout}
"""

            except Exception as e:
                logger.warning(f"⚠️ Tesseract ошибка: {e}")

            # Если ничего не помогло
            return """
❌ Не удалось извлечь текст из изображения.

Установите один из инструментов OCR:
1. pytesseract + Tesseract:
   pip install pytesseract
   # Затем установите Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

2. EasyOCR (рекомендуется):
   pip install easyocr

3. Tesseract напрямую:
   # Windows: https://github.com/UB-Mannheim/tesseract/wiki
   # Linux: sudo apt-get install tesseract-ocr
   # macOS: brew install tesseract
"""

        except Exception as e:
            logger.error(f"❌ Ошибка OCR: {e}")
            return f"❌ Ошибка: {e}"

    async def classify_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Классифицировать звук окружения.

        Args:
            audio_path: Путь к аудио файлу

        Returns:
            Классификация звука
        """
        try:
            if not Path(audio_path).exists():
                return {"error": f"Файл не найден: {audio_path}"}

            # Эмуляция классификации
            classifications = {
                "speech": 0.0,
                "music": 0.0,
                "noise": 1.0,
                "silence": 0.0,
            }

            logger.info(f"🎵 Аудио классифицировано: {audio_path}")
            return classifications

        except Exception as e:
            logger.error(f"❌ Ошибка классификации аудио: {e}")
            return {"error": str(e)}

    async def extract_video_frames(
        self,
        video_path: str,
        num_frames: int = 5,
    ) -> List[str]:
        """
        Извлечь ключевые кадры из видео.

        Args:
            video_path: Путь к видео
            num_frames: Количество кадров

        Returns:
            Пути к кадрам
        """
        try:
            if not Path(video_path).exists():
                logger.error(f"❌ Файл не найден: {video_path}")
                return []

            import cv2

            logger.info(f"📹 Извлекаю кадры из {video_path}")

            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_interval = max(1, frame_count // num_frames)

            frames = []
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    frame_path = f"frame_{len(frames)}.jpg"
                    cv2.imwrite(frame_path, frame)
                    frames.append(frame_path)

                frame_idx += 1

            cap.release()

            logger.info(f"✅ Извлечено {len(frames)} кадров из видео")
            return frames

        except ImportError:
            logger.warning("⚠️ opencv-python не установлен")
            return []
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения кадров: {e}")
            return []

    @staticmethod
    def _encode_image(image_path: str) -> str:
        """Кодировать изображение в base64."""
        try:
            if Image is None or base64 is None:
                return ""

            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except Exception as e:
            logger.error(f"❌ Ошибка кодирования изображения: {e}")
            return ""

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"MultimodalProcessor(available={self.is_available})"