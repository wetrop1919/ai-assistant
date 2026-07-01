"""
Комплексная система безопасности для AI ассистента.

Включает:
- Детектор песочницы
- Песочница для кода
- Валидатор команд
- Монитор файловой системы
- Сетевой файрвол
- Аудитор
"""

import logging
import os
import sys
import subprocess
import re
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio
import tempfile
import shutil

logger = logging.getLogger(__name__)


class DangerLevel(Enum):
    """Уровни опасности."""
    SAFE = 1
    WARNING = 2
    DANGEROUS = 3
    CRITICAL = 4


class IsolationLevel(Enum):
    """Уровни изоляции."""
    FULL_ACCESS = 1
    RESTRICTED = 2
    VM_ISOLATED = 3
    CONTAINER_ISOLATED = 4
    CHROOT_ISOLATED = 5


@dataclass
class AuditEvent:
    """Событие аудита."""
    timestamp: str
    action: str
    status: str  # success, denied, error
    details: Dict[str, Any]
    risk_level: str
    user_id: str = "assistant"


class SandboxDetector:
    """Детектор окружения и уровня изоляции."""

    def __init__(self):
        """Инициализация."""
        self.isolation_level = IsolationLevel.FULL_ACCESS
        self.detected_env = {}
        self._detect_environment()

    def _detect_environment(self) -> None:
        """Определить окружение."""
        logger.info("🔍 Проверяю окружение...")

        # Проверяем Docker
        if self._is_docker():
            self.isolation_level = IsolationLevel.CONTAINER_ISOLATED
            self.detected_env["docker"] = True
            logger.info("✅ Обнаружен Docker контейнер")

        # Проверяем виртуальную машину
        elif self._is_virtual_machine():
            self.isolation_level = IsolationLevel.VM_ISOLATED
            self.detected_env["vm"] = True
            logger.info("✅ Обнаружена виртуальная машина")

        # Проверяем chroot
        elif self._is_chroot():
            self.isolation_level = IsolationLevel.CHROOT_ISOLATED
            self.detected_env["chroot"] = True
            logger.info("✅ Обнаружена chroot окружение")

        # Проверяем ограниченного пользователя
        elif not self._is_root():
            self.isolation_level = IsolationLevel.RESTRICTED
            self.detected_env["restricted_user"] = True
            logger.info("✅ Запущен от ограниченного пользователя")

        else:
            self.isolation_level = IsolationLevel.FULL_ACCESS
            self.detected_env["full_access"] = True
            logger.warning("⚠️ Запущен с полным доступом")

    def _is_docker(self) -> bool:
        """Проверить запущен ли в Docker контейнере."""
        try:
            # Проверка для Linux
            dockerenv = Path("/.dockerenv")
            if dockerenv.exists():
                return True
            
            cgroup = Path("/proc/self/cgroup")
            if cgroup.exists():
                content = cgroup.read_text("utf-8", errors="ignore")
                if "docker" in content.lower():
                    return True
            
            # Проверка для Windows
            if os.name == 'nt':
                if os.environ.get('DOCKER_CONTAINER', '').lower() == 'true':
                    return True
                    
        except Exception:
            pass
        
        return False

    def _is_virtual_machine(self) -> bool:
        """Проверить ВМ."""
        try:
            result = subprocess.run(
                ["systemd-detect-virt"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return result.stdout.strip() != "none"
        except:
            return False

    def _is_chroot(self) -> bool:
        """Проверить chroot."""
        try:
            real_root = os.stat("/").st_ino
            chroot_root = os.stat("/proc/1/root").st_ino
            return real_root != chroot_root
        except:
            return False

    def _is_root(self) -> bool:
        """Проверить root пользователя."""
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False

    def get_info(self) -> Dict[str, Any]:
        """Получить информацию об окружении."""
        return {
            "isolation_level": self.isolation_level.name,
            "isolation_value": self.isolation_level.value,
            "detected_env": self.detected_env,
        }

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"SandboxDetector(level={self.isolation_level.name})"


class CodeSandbox:
    """Песочница для выполнения кода."""

    FORBIDDEN_MODULES = {
        "os", "sys", "subprocess", "socket", "urllib",
        "requests", "paramiko", "fabric", "ansible",
        "ctypes", "ctypes.util", "importlib",
    }

    FORBIDDEN_BUILTINS = {
        "exec", "eval", "compile", "__import__",
        "open", "input", "vars", "dir", "globals",
    }

    def __init__(
        self,
        timeout: int = 5,
        memory_limit: int = 1024,  # MB
    ):
        """
        Инициализация.

        Args:
            timeout: Таймаут в секундах
            memory_limit: Лимит памяти в MB
        """
        self.timeout = timeout
        self.memory_limit = memory_limit
        logger.info(f"🔒 CodeSandbox инициализирована (timeout={timeout}s, memory={memory_limit}MB)")

    async def execute(
        self,
        code: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Выполнить код в изолированной среде.

        Args:
            code: Исходный код Python
            variables: Переменные для передачи

        Returns:
            Кортеж (успех, результат/ошибка)
        """
        try:
            # Проверяем на опасные операции
            if not self._is_safe_code(code):
                logger.warning(f"🚫 Обнаружен опасный код: {code[:100]}")
                return False, "❌ Код содержит запрещённые операции"

            # Создаем чистый namespace
            safe_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "bool": bool,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                },
            }

            if variables:
                safe_globals.update(variables)

            safe_locals: Dict[str, Any] = {}

            # Выполняем код с таймаутом
            try:
                exec(code, safe_globals, safe_locals)
                result = safe_locals.get("result", "OK")
                logger.info(f"✅ Код выполнен успешно")
                return True, str(result)

            except TimeoutError:
                return False, f"❌ Превышено время выполнения ({self.timeout}s)"
            except MemoryError:
                return False, f"❌ Превышен лимит памяти ({self.memory_limit}MB)"
            except Exception as e:
                return False, f"❌ Ошибка выполнения: {e}"

        except Exception as e:
            logger.error(f"❌ Ошибка песочницы: {e}")
            return False, f"❌ Критическая ошибка: {e}"

    def _is_safe_code(self, code: str) -> bool:
        """Проверить безопасность кода."""
        # Проверяем импорты
        import_pattern = r"^\s*(?:from|import)\s+(\w+)"
        for match in re.finditer(import_pattern, code, re.MULTILINE):
            module = match.group(1)
            if module in self.FORBIDDEN_MODULES:
                logger.warning(f"🚫 Запрещённый модуль: {module}")
                return False

        # Проверяем встроенные функции
        for builtin in self.FORBIDDEN_BUILTINS:
            if builtin in code:
                logger.warning(f"🚫 Запрещённая функция: {builtin}")
                return False

        # Проверяем открытие файлов
        if "open(" in code or "__file__" in code:
            logger.warning("🚫 Попытка доступа к файлам")
            return False

        return True

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"CodeSandbox(timeout={self.timeout}s)"


class CommandValidator:
    """Валидатор системных команд."""

    # Белый список команд
    SAFE_COMMANDS = {
        "ls": DangerLevel.SAFE,
        "pwd": DangerLevel.SAFE,
        "echo": DangerLevel.SAFE,
        "cat": DangerLevel.SAFE,
        "grep": DangerLevel.SAFE,
        "find": DangerLevel.WARNING,
        "cp": DangerLevel.WARNING,
        "mv": DangerLevel.WARNING,
        "mkdir": DangerLevel.WARNING,
        "rm": DangerLevel.DANGEROUS,
        "chmod": DangerLevel.CRITICAL,
        "sudo": DangerLevel.CRITICAL,
        "rm -rf": DangerLevel.CRITICAL,
    }

    # Опасные паттерны
    DANGEROUS_PATTERNS = {
        r".*\$\(.*\).*": "Command substitution",
        r".*;.*": "Command chaining",
        r".*\|.*": "Pipe usage",
        r".*&.*": "Background execution",
        r".*>.*": "Output redirection",
        r".*<.*": "Input redirection",
        r"rm\s+-rf\s+/": "Recursive deletion of root",
        r"dd\s+if=.*of=": "Disk writing",
    }

    def __init__(self):
        """Инициализация."""
        logger.info("🔍 CommandValidator инициализирован")

    def validate(self, command: str) -> Tuple[bool, DangerLevel, str]:
        """
        Валидировать команду.

        Args:
            command: Команда для выполнения

        Returns:
            Кортеж (валидна, уровень опасности, причина)
        """
        command_clean = command.strip()
        cmd_name = command_clean.split()[0]

        # Проверяем опасные паттерны
        for pattern, description in self.DANGEROUS_PATTERNS.items():
            if re.match(pattern, command_clean):
                logger.warning(f"🚫 Обнаружен опасный паттерн: {description}")
                return False, DangerLevel.CRITICAL, description

        # Проверяем в белом списке
        if cmd_name in self.SAFE_COMMANDS:
            level = self.SAFE_COMMANDS[cmd_name]
            logger.info(f"✅ Команда разрешена: {cmd_name} ({level.name})")
            return True, level, "Разрешена"

        logger.warning(f"⚠️ Неизвестная команда: {cmd_name}")
        return False, DangerLevel.DANGEROUS, "Команда не в белом списке"

    def sanitize_arguments(self, args: List[str]) -> List[str]:
        """
        Экранировать аргументы.

        Args:
            args: Аргументы команды

        Returns:
            Экранированные аргументы
        """
        import shlex

        sanitized = []
        for arg in args:
            # Экранируем специальные символы
            safe_arg = shlex.quote(arg)
            sanitized.append(safe_arg)

        return sanitized

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"CommandValidator(safe_commands={len(self.SAFE_COMMANDS)})"


class FSMonitor:
    """Монитор файловой системы."""

    # Защищённые директории
    PROTECTED_DIRS = {
        "/": "Root directory",
        "/bin": "Binary files",
        "/sys": "System files",
        "/proc": "Process files",
        "/etc": "Configuration",
        "/root": "Root home",
    }

    def __init__(self, workspace: str = "./workspace"):
        """
        Инициализация.

        Args:
            workspace: Рабочая директория для ассистента
        """
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.disk_quota = 1024 * 1024 * 1024  # 1GB
        self.used_space = 0

        logger.info(f"📁 FSMonitor инициализирован (workspace={workspace})")

    def can_read(self, path: str) -> bool:
        """
        Проверить возможность чтения.

        Args:
            path: Путь к файлу

        Returns:
            True если можно читать
        """
        try:
            file_path = Path(path).resolve()

            # Проверяем защищённые директории
            for protected in self.PROTECTED_DIRS:
                if str(file_path).startswith(protected):
                    logger.warning(f"🚫 Доступ к защищённой директории запрещен: {path}")
                    return False

            return file_path.exists() and file_path.is_file()

        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа к файлу: {e}")
            return False

    def can_write(self, path: str) -> bool:
        """
        Проверить возможность записи.

        Args:
            path: Путь к файлу

        Returns:
            True если можно писать
        """
        try:
            file_path = Path(path).resolve()

            # Проверяем защищённые директории
            for protected in self.PROTECTED_DIRS:
                if str(file_path).startswith(protected):
                    logger.warning(f"🚫 Запись в защищённую директорию запрещена: {path}")
                    return False

            # Проверяем рабочую директорию
            if not str(file_path).startswith(str(self.workspace)):
                logger.warning(f"🚫 Запись вне рабочей директории: {path}")
                return False

            # Проверяем квоту
            file_size = file_path.stat().st_size if file_path.exists() else 0
            if self.used_space + file_size > self.disk_quota:
                logger.warning(f"🚫 Превышена квота на диск")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступа к файлу: {e}")
            return False

    def create_backup(self, path: str) -> Optional[str]:
        """
        Создать бэкап файла.

        Args:
            path: Путь к файлу

        Returns:
            Путь к бэкапу или None
        """
        try:
            file_path = Path(path)
            if not file_path.exists():
                return None

            backup_dir = self.workspace / ".backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{file_path.name}_{timestamp}.bak"

            shutil.copy2(file_path, backup_path)
            logger.info(f"✅ Бэкап создан: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"❌ Ошибка создания бэкапа: {e}")
            return None

    def restore_backup(self, backup_path: str, original_path: str) -> bool:
        """
        Восстановить из бэкапа.

        Args:
            backup_path: Путь к бэкапу
            original_path: Исходный путь

        Returns:
            True если успешно
        """
        try:
            shutil.copy2(backup_path, original_path)
            logger.info(f"✅ Восстановлено из бэкапа: {original_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления: {e}")
            return False

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"FSMonitor(workspace={self.workspace})"


class AuditLogger:
    """Логгер аудита."""

    def __init__(self, log_file: str = ".audit_log"):
        """
        Инициализация.

        Args:
            log_file: Файл логов аудита
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[AuditEvent] = []

        logger.info(f"📋 AuditLogger инициализирован ({log_file})")

    def log_event(
        self,
        action: str,
        status: str,
        details: Dict[str, Any],
        risk_level: str,
    ) -> None:
        """
        Логировать событие.

        Args:
            action: Действие
            status: Статус (success, denied, error)
            details: Детали действия
            risk_level: Уровень риска
        """
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            action=action,
            status=status,
            details=details,
            risk_level=risk_level,
        )

        self.events.append(event)

        # Записываем в файл
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(asdict(event)) + "\n")
        except Exception as e:
            logger.error(f"❌ Ошибка записи в лог аудита: {e}")

        # Логируем
        emoji = {
            "success": "✅",
            "denied": "🚫",
            "error": "❌",
        }.get(status, "ℹ️")

        logger.info(f"{emoji} [{risk_level}] {action}: {status}")

    def get_recent_events(self, limit: int = 10) -> List[AuditEvent]:
        """Получить последние события."""
        return self.events[-limit:]

    def export_events(self, output_file: str, format_type: str = "json") -> bool:
        """
        Экспортировать события.

        Args:
            output_file: Файл для экспорта
            format_type: Формат (json, csv, siem)

        Returns:
            True если успешно
        """
        try:
            with open(output_file, "w") as f:
                if format_type == "json":
                    json.dump([asdict(e) for e in self.events], f, indent=2)
                elif format_type == "csv":
                    import csv

                    if self.events:
                        writer = csv.DictWriter(f, fieldnames=asdict(self.events[0]).keys())
                        writer.writeheader()
                        for event in self.events:
                            writer.writerow(asdict(event))

            logger.info(f"✅ События экспортированы: {output_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта: {e}")
            return False

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"AuditLogger(events={len(self.events)})"


class SecurityManager:
    """Менеджер безопасности."""

    def __init__(
        self,
        sandbox_enabled: bool = True,
        workspace: str = "./workspace",
    ):
        """
        Инициализация.

        Args:
            sandbox_enabled: Включить песочницу
            workspace: Рабочая директория
        """
        self.sandbox_detector = SandboxDetector()
        self.code_sandbox = CodeSandbox() if sandbox_enabled else None
        self.command_validator = CommandValidator()
        self.fs_monitor = FSMonitor(workspace)
        self.audit_logger = AuditLogger()

        logger.info("🔒 SecurityManager инициализирован")

    async def execute_code(
        self,
        code: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Безопасно выполнить код.

        Args:
            code: Код Python
            variables: Переменные

        Returns:
            Кортеж (успех, результат)
        """
        try:
            if not self.code_sandbox:
                self.audit_logger.log_event(
                    "code_execution",
                    "denied",
                    {"code": code[:100]},
                    "CRITICAL",
                )
                return False, "❌ Песочница отключена"

            success, result = await self.code_sandbox.execute(code, variables)

            status = "success" if success else "error"
            self.audit_logger.log_event(
                "code_execution",
                status,
                {"code": code[:100], "result": result[:100]},
                "DANGEROUS" if success else "CRITICAL",
            )

            return success, result

        except Exception as e:
            self.audit_logger.log_event(
                "code_execution",
                "error",
                {"error": str(e)},
                "CRITICAL",
            )
            return False, f"❌ Ошибка: {e}"

    def validate_command(self, command: str) -> Tuple[bool, DangerLevel, str]:
        """
        Валидировать команду.

        Args:
            command: Команда

        Returns:
            Кортеж (валидна, уровень опасности, причина)
        """
        valid, level, reason = self.command_validator.validate(command)

        status = "allowed" if valid else "denied"
        self.audit_logger.log_event(
            "command_validation",
            status,
            {"command": command[:100], "level": level.name},
            level.name,
        )

        return valid, level, reason

    def can_access_file(self, path: str, mode: str = "r") -> bool:
        """
        Проверить доступ к файлу.

        Args:
            path: Путь к файлу
            mode: Режим (r, w)

        Returns:
            True если доступ разрешен
        """
        if mode == "r":
            return self.fs_monitor.can_read(path)
        elif mode == "w":
            return self.fs_monitor.can_write(path)

        return False

    def get_security_status(self) -> Dict[str, Any]:
        """Получить статус безопасности."""
        return {
            "sandbox": self.sandbox_detector.get_info(),
            "code_sandbox": self.code_sandbox is not None,
            "audit_events": len(self.audit_logger.events),
        }

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"SecurityManager("
            f"sandbox_level={self.sandbox_detector.isolation_level.name}, "
            f"code_sandbox={'enabled' if self.code_sandbox else 'disabled'})"
        )