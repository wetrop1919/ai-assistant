"""
Базовые быстрые тесты без сложных зависимостей.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pytest
from utils import TextFormatter, AsciiArt, ProgressBar


class TestUtils:
    """Тесты утилит."""

    def test_format_duration(self):
        """Тест форматирования длительности."""
        assert TextFormatter.format_duration(30) == "30.0с"
        assert TextFormatter.format_duration(90).endswith("м")
        assert TextFormatter.format_duration(3600).endswith("ч")

    def test_truncate(self):
        """Тест обрезания текста."""
        result = TextFormatter.truncate("Hello World", max_length=5)
        assert len(result) <= 8  # "Hello..." = 8
        assert result.endswith("...")

    def test_truncate_short(self):
        """Тест обрезания короткого текста."""
        result = TextFormatter.truncate("Hi", max_length=10)
        assert result == "Hi"

    def test_format_box(self):
        """Тест форматирования текста в рамку."""
        result = TextFormatter.format_box("Test")
        assert "┌" in result
        assert "└" in result
        assert "Test" in result

    def test_ascii_art_banner(self):
        """Тест ASCII арта баннера."""
        banner = AsciiArt.BANNER
        assert "AI ASSISTANT" in banner

    def test_ascii_art_methods(self):
        """Тест методов ASCII арта."""
        # Эти методы не должны вызывать ошибки
        AsciiArt.print_separator()
        AsciiArt.print_listening()
        AsciiArt.print_thinking()
        AsciiArt.print_speaking()


class TestConfig:
    """Тесты конфигурации."""

    def test_config_loading(self):
        """Тест загрузки конфигурации."""
        from config import config

        assert config is not None
        assert config.version is not None
        assert config.mode is not None


class TestLogger:
    """Тесты логирования."""

    def test_logger_creation(self):
        """Тест создания логгера."""
        from logger import get_logger

        logger = get_logger(__name__)
        assert logger is not None

        # Тестируем логирование
        logger.info("Test message")
        logger.warning("Test warning")
        logger.error("Test error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])