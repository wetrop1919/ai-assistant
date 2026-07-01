"""
Конфигурация приложения из переменных окружения (.env).

Использует pydantic для валидации и type hints.
"""

from pathlib import Path
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
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
    keep_alive: str = Field(default="5m", env="OLLAMA_KEEP_ALIVE")

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


class SecurityConfig(BaseSettings):
    """Конфигурация безопасности."""

    sandbox_enabled: bool = Field(default=True, env="SECURITY_SANDBOX_ENABLED")
    sandbox_level: str = Field(default="auto", env="SECURITY_SANDBOX_LEVEL")
    code_execution: str = Field(default="sandbox", env="SECURITY_CODE_EXECUTION")
    network_access: str = Field(default="whitelist", env="SECURITY_NETWORK_ACCESS")
    file_access: str = Field(default="workspace_only", env="SECURITY_FILE_ACCESS")
    require_confirmation: List[str] = Field(
        default=["DANGEROUS", "CRITICAL"],
        env="SECURITY_REQUIRE_CONFIRMATION"
    )
    auto_deny_timeout: int = Field(default=30, env="SECURITY_AUTO_DENY_TIMEOUT")
    audit_log_level: str = Field(default="INFO", env="SECURITY_AUDIT_LOG_LEVEL")
    audit_log_file: str = Field(default=".audit_log", env="SECURITY_AUDIT_LOG_FILE")
    telemetry_enabled: bool = Field(default=False, env="SECURITY_TELEMETRY_ENABLED")
    cpu_limit: int = Field(default=50, env="SECURITY_CPU_LIMIT")
    memory_limit: int = Field(default=512, env="SECURITY_MEMORY_LIMIT")
    disk_limit: int = Field(default=1024, env="SECURITY_DISK_LIMIT")
    workspace_dir: str = Field(default="./workspace", env="SECURITY_WORKSPACE_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class IntegrationsConfig(BaseSettings):
    """Конфигурация интеграций."""

    # Calendar
    calendar_enabled: bool = Field(default=False, env="CALENDAR_ENABLED")
    google_calendar_key: str = Field(default="", env="GOOGLE_CALENDAR_KEY")

    # Email
    email_enabled: bool = Field(default=False, env="EMAIL_ENABLED")
    imap_server: str = Field(default="", env="IMAP_SERVER")
    imap_port: int = Field(default=993, env="IMAP_PORT")
    email_address: str = Field(default="", env="EMAIL_ADDRESS")
    email_password: str = Field(default="", env="EMAIL_PASSWORD")

    # Todo
    todo_enabled: bool = Field(default=False, env="TODO_ENABLED")
    todoist_token: str = Field(default="", env="TODOIST_TOKEN")

    # Smart Home
    smart_home_enabled: bool = Field(default=False, env="SMART_HOME_ENABLED")
    home_assistant_url: str = Field(default="", env="HOME_ASSISTANT_URL")
    home_assistant_token: str = Field(default="", env="HOME_ASSISTANT_TOKEN")
    mqtt_broker: str = Field(default="", env="MQTT_BROKER")

    # Media
    media_enabled: bool = Field(default=False, env="MEDIA_ENABLED")
    spotify_client_id: str = Field(default="", env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(default="", env="SPOTIFY_CLIENT_SECRET")

    # Notifications
    notifier_enabled: bool = Field(default=False, env="NOTIFIER_ENABLED")
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", env="TELEGRAM_CHAT_ID")
    slack_webhook: str = Field(default="", env="SLACK_WEBHOOK")
    discord_webhook: str = Field(default="", env="DISCORD_WEBHOOK")

    def __getattr__(self, name: str):
        """Совместимость с заглавными названиями."""
        # Преобразуем CALENDAR_ENABLED -> calendar_enabled
        lower_name = name.lower()
        if lower_name != name and hasattr(self, lower_name):
            return getattr(self, lower_name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

class AppConfig(BaseSettings):
    """Главная конфигурация приложения."""

    version: str = Field(default="0.2.0", env="PROJECT_VERSION")
    name: str = Field(default="AI Assistant", env="PROJECT_NAME")
    debug: bool = Field(default=False, env="DEBUG")

    # Подконфигурации
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    speech: SpeechConfig = Field(default_factory=SpeechConfig)
    mode: ModeConfig = Field(default_factory=ModeConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Глобальная конфигурация (синоним для совместимости)
config = AppConfig()

# Алиас для совместимости с main.py
Config = AppConfig

logger.info(f"✅ Конфигурация загружена: {config.name} v{config.version}")
logger.debug(
    f"Режимы: CLI={config.mode.cli_mode}, "
    f"Voice={config.mode.voice_mode}, "
    f"Sandbox={config.mode.sandbox_mode}"
)
logger.debug(f"Ollama: {config.ollama.host}")