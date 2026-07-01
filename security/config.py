"""
Конфигурация безопасности.
"""

import logging
from typing import Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field

logger = logging.getLogger(__name__)


class SecurityConfig(BaseSettings):
    """Конфигурация безопасности."""

    # Основные параметры
    sandbox_enabled: bool = Field(default=True, env="SECURITY_SANDBOX_ENABLED")
    sandbox_level: str = Field(default="auto", env="SECURITY_SANDBOX_LEVEL")  # auto, 1-5

    # Выполнение кода
    code_execution: str = Field(default="sandbox", env="SECURITY_CODE_EXECUTION")
    # disabled, sandbox, full

    # Сетевой доступ
    network_access: str = Field(default="whitelist", env="SECURITY_NETWORK_ACCESS")
    # blocked, whitelist, full

    # Доступ к файлам
    file_access: str = Field(default="workspace_only", env="SECURITY_FILE_ACCESS")
    # readonly, workspace, full

    # Подтверждение
    require_confirmation: list = Field(
        default=["DANGEROUS", "CRITICAL"],
        env="SECURITY_REQUIRE_CONFIRMATION"
    )
    auto_deny_timeout: int = Field(default=30, env="SECURITY_AUTO_DENY_TIMEOUT")

    # Аудит
    audit_log_level: str = Field(default="INFO", env="SECURITY_AUDIT_LOG_LEVEL")
    audit_log_file: str = Field(default=".audit_log", env="SECURITY_AUDIT_LOG_FILE")

    # Телеметрия
    telemetry_enabled: bool = Field(default=False, env="SECURITY_TELEMETRY_ENABLED")

    # Лимиты ресурсов
    cpu_limit: int = Field(default=50, env="SECURITY_CPU_LIMIT")  # %
    memory_limit: int = Field(default=512, env="SECURITY_MEMORY_LIMIT")  # MB
    disk_limit: int = Field(default=1024, env="SECURITY_DISK_LIMIT")  # MB

    # Белые списки
    allowed_domains: list = Field(default=[], env="SECURITY_ALLOWED_DOMAINS")
    allowed_processes: list = Field(default=[], env="SECURITY_ALLOWED_PROCESSES")

    # Рабочая директория
    workspace_dir: str = Field(default="./workspace", env="SECURITY_WORKSPACE_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # ← ДОБАВЬ ЭТУ СТРОКУ

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return self.dict()

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"SecurityConfig("
            f"sandbox={self.sandbox_enabled}, "
            f"level={self.sandbox_level})"
        )