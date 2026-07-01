"""
Политики безопасности для различных сценариев.
"""

import logging
import copy
from typing import Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class PolicyProfile(Enum):
    """Профили политик."""
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"
    CUSTOM = "custom"


@dataclass
class SecurityPolicy:
    """Политика безопасности."""
    name: str
    description: str
    sandbox_level: int = 3  # 1-5
    code_execution: str = "sandbox"  # disabled, sandbox, full
    network_access: str = "whitelist"  # blocked, whitelist, full
    file_access: str = "workspace_only"  # readonly, workspace, full
    require_confirmation: List[str] = field(default_factory=lambda: ["DANGEROUS", "CRITICAL"])
    auto_deny_timeout: int = 30
    audit_log_level: str = "INFO"
    telemetry: bool = False
    cpu_limit: int = 50  # процент
    memory_limit: int = 512  # MB
    disk_limit: int = 1024  # MB
    network_bandwidth: int = 10  # Mbps
    allowed_domains: List[str] = field(default_factory=list)
    allowed_processes: List[str] = field(default_factory=list)


# Предустановленные политики
POLICIES: Dict[PolicyProfile, SecurityPolicy] = {
    PolicyProfile.STRICT: SecurityPolicy(
        name="strict",
        description="Максимальные ограничения для безопасности",
        sandbox_level=5,
        code_execution="sandbox",
        network_access="blocked",
        file_access="readonly",
        require_confirmation=["WARNING", "DANGEROUS", "CRITICAL"],
        auto_deny_timeout=30,
        cpu_limit=25,
        memory_limit=256,
        disk_limit=512,
    ),
    PolicyProfile.BALANCED: SecurityPolicy(
        name="balanced",
        description="Сбалансированная политика для обычного использования",
        sandbox_level=3,
        code_execution="sandbox",
        network_access="whitelist",
        file_access="workspace_only",
        require_confirmation=["DANGEROUS", "CRITICAL"],
        auto_deny_timeout=30,
        cpu_limit=50,
        memory_limit=512,
        disk_limit=1024,
    ),
    PolicyProfile.PERMISSIVE: SecurityPolicy(
        name="permissive",
        description="Мало ограничений для разработки и тестирования",
        sandbox_level=1,
        code_execution="full",
        network_access="full",
        file_access="full",
        require_confirmation=["CRITICAL"],
        auto_deny_timeout=60,
        cpu_limit=100,
        memory_limit=2048,
        disk_limit=5120,
    ),
}


class PolicyManager:
    """Менеджер политик."""

    def __init__(self, profile: PolicyProfile = PolicyProfile.BALANCED):
        """
        Инициализация.

        Args:
            profile: Начальный профиль
        """
        self.current_profile = profile
        self.current_policy = copy.deepcopy(POLICIES[profile])
        logger.info(f"📋 PolicyManager инициализирован ({profile.value})")

    def get_policy(self) -> SecurityPolicy:
        """Получить текущую политику."""
        return self.current_policy

    def set_profile(self, profile: PolicyProfile) -> None:
        """Установить профиль."""
        if profile in POLICIES:
            self.current_profile = profile
            self.current_policy = copy.deepcopy(POLICIES[profile])
            logger.info(f"✅ Профиль изменен: {profile.value}")
        else:
            logger.warning(f"⚠️ Неизвестный профиль: {profile}")

    def customize(self, **kwargs) -> None:
        """
        Кастомизировать политику.

        Args:
            **kwargs: Параметры политики
        """
        for key, value in kwargs.items():
            if hasattr(self.current_policy, key):
                setattr(self.current_policy, key, value)
                logger.info(f"✅ Параметр обновлен: {key}={value}")
            else:
                logger.warning(f"⚠️ Неизвестный параметр: {key}")

    def check_permission(self, action: str, risk_level: str) -> bool:
        """
        Проверить разрешение на действие.

        Args:
            action: Действие
            risk_level: Уровень риска

        Returns:
            True если разрешено
        """
        if risk_level in self.current_policy.require_confirmation:
            logger.info(f"⚠️ Требуется подтверждение для: {action}")
            return False

        return True

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"PolicyManager(profile={self.current_profile.value})"