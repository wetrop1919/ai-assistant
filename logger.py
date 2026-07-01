"""
Модуль логирования с цветным выводом.

Предоставляет единую точку конфигурации логирования для всего приложения.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import colorlog

# Типы для type hints
LogLevel = str


def setup_logger(
    name: str = "ai_assistant",
    log_file: str = "assistant.log",
    log_level: str = "INFO",
    log_format: str = "detailed",
) -> logging.Logger:
    """
    Настройка логгера с поддержкой цвета и файлового вывода.

    Args:
        name: Имя логгера
        log_file: Путь к файлу логов
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Формат логов (detailed или simple)

    Returns:
        Настроенный logger объект
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Удаляем существующих обработчиков
    logger.handlers.clear()

    # Форматы логов
    if log_format == "detailed":
        console_format = (
            "%(log_color)s[%(asctime)s]%(reset)s "
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(log_color)s%(name)s:%(funcName)s:%(lineno)d%(reset)s "
            "%(message)s"
        )
        file_format = (
            "[%(asctime)s] %(levelname)-8s "
            "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )
    else:  # simple
        console_format = (
            "%(log_color)s[%(levelname)s]%(reset)s %(message)s"
        )
        file_format = "[%(levelname)s] %(message)s"

    # Консольный обработчик с цветом
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(
        colorlog.ColoredFormatter(
            fmt=console_format,
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )
    )
    logger.addHandler(console_handler)

    # Файловый обработчик
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter(fmt=file_format, datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(file_handler)

    return logger


# Глобальный logger
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер для модуля.

    Args:
        name: Имя модуля (__name__)

    Returns:
        Logger объект
    """
    return logging.getLogger(name)
