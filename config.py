"""
Конфигурация приложения из переменных окружения (.env).

Использует pydantic для валидации и type hints.
"""

from pathlib import Path
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from security.config import SecurityConfig
import logging

# Загружаем .env файл
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

logger = logging.getLogger(__name__)


class OllamaConfig(BaseSettings):
    """Конфигурация Ollama."""

    host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    model: str = Field(default="llama3:8b", env="OLLAMA_MODEL")
    code_model: str = Field(default="codellama:13b", env="OLLAMA_CODE_MODEL")
    fast_model: str = Field(default="phi3:mini", env="OLLAMA_FAST_MODEL")
    timeout: int = Field(default=30, env="OLLAMA_TIMEOUT")
    temperature_general: float = Field(
        default=0.7, env="OLLAMA_TEMPERATURE_GENERAL"
    )
    temperature_code: float = Field(
        default=0.2, env="OLLAMA_TEMPERATURE_CODE"
    )

    @validator("temperature_general", "temperature_code")
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Temperature должна быть между 0.0 и 1.0")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class SpeechConfig(BaseSettings):
    """Конфигурация речевых параметров."""

    wake_words: List[str] = Field(
        default=["ассистент", "слушай", "компьютер"],
        env="WAKE_WORDS"
    )
    wake_word_confidence: float = Field(
        default=0.90, env="WAKE_WORD_CONFIDENCE"
    )

    # Speech-to-Text
    whisper_model: str = Field(default="medium", env="WHISPER_MODEL")
    whisper_language: str = Field(default="ru", env="WHISPER_LANGUAGE")
    whisper_device: str = Field(default="cpu", env="WHISPER_DEVICE")

    # Text-to-Speech
    tts_engine: str = Field(default="pyttsx3", env="TTS_ENGINE")
    tts_language: str = Field(default="ru", env="TTS_LANGUAGE")
    tts_voice_rate: int = Field(default=150, env="TTS_VOICE_RATE")
    tts_volume: float = Field(default=1.0, env="TTS_VOLUME")
    piper_model: str = Field(default="ru_RU", env="PIPER_MODEL")

    @validator("wake_words", pre=True)
    def parse_wake_words(cls, v):
        if isinstance(v, str):
            return [w.strip() for w in v.split(",")]
        return v

    @validator("wake_word_confidence", "tts_volume")
    def validate_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Значение должно быть между 0.0 и 1.0")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class ModeConfig(BaseSettings):
    """Конфигурация режимов работы."""

    cli_mode: bool = Field(default=False, env="CLI_MODE")
    voice_mode: bool = Field(default=True, env="VOICE_MODE")
    sandbox_mode: bool = Field(default=True, env="SANDBOX_MODE")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class LoggingConfig(BaseSettings):
    """Конфигурация логирования."""

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="assistant.log", env="LOG_FILE")
    log_format: str = Field(default="detailed", env="LOG_FORMAT")

    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level должен быть одним из {valid_levels}")
        return v.upper()

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class MemoryConfig(BaseSettings):
    """Конфигурация памяти."""

    db_path: str = Field(default="memory.db", env="MEMORY_DB")
    short_term_size: int = Field(default=20, env="SHORT_TERM_MEMORY_SIZE")
    embedding_model: str = Field(
        default="ru_embedding", env="MEMORY_EMBEDDING_MODEL"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

class IntegrationsConfig(BaseSettings):
    """Конфигурация интеграций."""

    # Calendar
    CALENDAR_ENABLED: bool = Field(default=False, env="CALENDAR_ENABLED")
    GOOGLE_CALENDAR_KEY: str = Field(default="", env="GOOGLE_CALENDAR_KEY")

    # Email
    EMAIL_ENABLED: bool = Field(default=False, env="EMAIL_ENABLED")
    IMAP_SERVER: str = Field(default="", env="IMAP_SERVER")
    IMAP_PORT: int = Field(default=993, env="IMAP_PORT")
    EMAIL_ADDRESS: str = Field(default="", env="EMAIL_ADDRESS")
    EMAIL_PASSWORD: str = Field(default="", env="EMAIL_PASSWORD")

    # Todo
    TODO_ENABLED: bool = Field(default=False, env="TODO_ENABLED")
    TODOIST_TOKEN: str = Field(default="", env="TODOIST_TOKEN")

    # Smart Home
    SMART_HOME_ENABLED: bool = Field(default=False, env="SMART_HOME_ENABLED")
    HOME_ASSISTANT_URL: str = Field(default="", env="HOME_ASSISTANT_URL")
    HOME_ASSISTANT_TOKEN: str = Field(default="", env="HOME_ASSISTANT_TOKEN")
    MQTT_BROKER: str = Field(default="", env="MQTT_BROKER")

    # Media
    MEDIA_ENABLED: bool = Field(default=False, env="MEDIA_ENABLED")
    SPOTIFY_CLIENT_ID: str = Field(default="", env="SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: str = Field(default="", env="SPOTIFY_CLIENT_SECRET")

    # Notifications
    NOTIFIER_ENABLED: bool = Field(default=False, env="NOTIFIER_ENABLED")
    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(default="", env="TELEGRAM_CHAT_ID")
    SLACK_WEBHOOK: str = Field(default="", env="SLACK_WEBHOOK")
    DISCORD_WEBHOOK: str = Field(default="", env="DISCORD_WEBHOOK")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

class AppConfig(BaseSettings):
    """Главная конфигурация приложения."""

    version: str = Field(default="0.1.0", env="PROJECT_VERSION")
    name: str = Field(default="AI Assistant", env="PROJECT_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    integrations: IntegrationsConfig = IntegrationsConfig()

    # Подконфигурации
    ollama: OllamaConfig = OllamaConfig()
    speech: SpeechConfig = SpeechConfig()
    mode: ModeConfig = ModeConfig()
    logging: LoggingConfig = LoggingConfig()
    memory: MemoryConfig = MemoryConfig()
    security: SecurityConfig = SecurityConfig()

    class Config:
        env_file = ".env.example"
        case_sensitive = False
        extra = "ignore"


# Глобальная конфигурация
config = AppConfig()

logger.info(f"✅ Конфигурация загружена: {config.name} v{config.version}")
logger.debug(f"Режимы: CLI={config.mode.cli_mode}, "
             f"Voice={config.mode.voice_mode}, "
             f"Sandbox={config.mode.sandbox_mode}")
logger.debug(f"Ollama: {config.ollama.host}")
