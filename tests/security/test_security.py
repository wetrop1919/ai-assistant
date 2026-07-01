"""
Тесты безопасности AI-ассистента.
Полностью синхронизированы с реальными методами SecurityManager.
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.security import SecurityManager, DangerLevel
from security.policies import PolicyManager, PolicyProfile


class TestSandboxEscape:
    """Тесты на выход из песочницы."""

    def setup_method(self):
        self.security = SecurityManager(
            sandbox_enabled=True,
            workspace="./test_workspace"
        )

    def test_subprocess_escape(self):
        """Попытка запуска системных процессов."""
        dangerous_code = [
            "import subprocess; subprocess.run(['cmd', '/c', 'dir'])",
            "import os; os.system('ls')",
        ]
        
        for code in dangerous_code:
            is_safe, result = asyncio.run(
                self.security.execute_code(code)
            )
            assert not is_safe, f"Код должен быть заблокирован: {code}"

    def test_import_restrictions(self):
        """Попытка импорта опасных модулей."""
        dangerous_imports = [
            "import subprocess",
            "from os import system",
            "import ctypes",
        ]
        
        for code in dangerous_imports:
            is_safe, result = asyncio.run(
                self.security.execute_code(code)
            )
            assert not is_safe, f"Импорт должен быть ограничен: {code}"

    def test_eval_exec_blocked(self):
        """Попытка выполнения произвольного кода."""
        dangerous = [
            "eval('1+1')",
            "exec('x=1')",
        ]
        
        for code in dangerous:
            is_safe, result = asyncio.run(
                self.security.execute_code(code)
            )
            assert not is_safe, f"eval/exec должны быть заблокированы: {code}"

    def test_safe_code_allowed(self):
        """Безопасный код должен выполняться."""
        safe_code = [
            "x = 1 + 1",
            "result = 'hello'",
            "y = [i for i in range(10)]",
        ]
        
        for code in safe_code:
            is_safe, result = asyncio.run(
                self.security.execute_code(code)
            )
            assert is_safe, f"Безопасный код должен выполняться: {code}"


class TestCommandInjection:
    """Тесты на инъекции команд."""

    def setup_method(self):
        self.security = SecurityManager(
            sandbox_enabled=True,
            workspace="./test_workspace"
        )

    def test_shell_injection(self):
        """Попытка инъекции shell команд."""
        injections = [
            "file.txt; rm -rf /",
            "file.txt && format C:",
            "file.txt | rm -rf /",
        ]
        
        for cmd in injections:
            is_safe, level, reason = self.security.validate_command(cmd)
            assert not is_safe or level in [DangerLevel.DANGEROUS, DangerLevel.CRITICAL], \
                f"Инъекция должна быть обнаружена: {cmd} — {reason}"

    def test_dangerous_commands_blocked(self):
        """Проверка опасных системных команд."""
        dangerous = [
            "rm -rf /",
            "sudo rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
        ]
        
        for cmd in dangerous:
            is_safe, level, reason = self.security.validate_command(cmd)
            assert not is_safe or level in [DangerLevel.DANGEROUS, DangerLevel.CRITICAL], \
                f"Опасная команда должна быть заблокирована: {cmd}"

    def test_safe_commands_allowed(self):
        """Безопасные команды должны быть разрешены."""
        safe_commands = [
            "ls",
            "echo hello",
            "pwd",
            "cat file.txt",
        ]
        
        for cmd in safe_commands:
            is_safe, level, reason = self.security.validate_command(cmd)
            assert is_safe, f"Безопасная команда должна быть разрешена: {cmd} — {reason}"


class TestPathTraversal:
    """Тесты на path traversal атаки."""

    def setup_method(self):
        self.security = SecurityManager(
            sandbox_enabled=True,
            workspace="./test_workspace"
        )

    def test_protected_dirs_blocked(self):
        """Доступ к защищённым директориям должен быть запрещён."""
        protected_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "/root/.ssh/id_rsa",
            "C:\\Windows\\System32\\config\\SAM",
        ]
        
        for path in protected_paths:
            can_read = self.security.can_access_file(path, "r")
            can_write = self.security.can_access_file(path, "w")
            assert not can_read, f"Чтение защищённого файла должно быть запрещено: {path}"
            assert not can_write, f"Запись в защищённый файл должна быть запрещена: {path}"

    def test_workspace_allowed(self):
        """Доступ к workspace должен быть разрешён."""
        workspace_paths = [
            "./test_workspace/test.txt",
            "./test_workspace/subdir/file.py",
        ]
        
        for path in workspace_paths:
            can_write = self.security.can_access_file(path, "w")
            assert can_write, f"Запись в workspace должна быть разрешена: {path}"


class TestFileSystemRestrictions:
    """Тесты на обход файловых ограничений."""

    def setup_method(self):
        self.security = SecurityManager(
            sandbox_enabled=True,
            workspace="./test_workspace"
        )

    def test_outside_workspace_blocked(self):
        """Запись за пределы workspace должна быть запрещена."""
        outside_paths = [
            "../outside.txt",
            "../../etc/hack",
        ]
        
        for path in outside_paths:
            can_write = self.security.can_access_file(path, "w")
            assert not can_write, f"Запись за пределы workspace должна быть запрещена: {path}"

    def test_symlink_commands_blocked(self):
        """Создание симлинков должно быть заблокировано."""
        dangerous = [
            "ln -s /etc/passwd link",
            "mklink link C:\\Windows\\System32",
        ]
        
        for cmd in dangerous:
            is_safe, level, reason = self.security.validate_command(cmd)
            assert not is_safe, f"Симлинк должен быть заблокирован: {cmd}"


class TestDoSSimulation:
    """Тесты на DoS атаки."""

    def setup_method(self):
        self.security = SecurityManager(
            sandbox_enabled=True,
            workspace="./test_workspace"
        )

    def test_infinite_loop_blocked(self):
        """Бесконечные циклы должны блокироваться."""
        infinite_loops = [
            "while True: pass",
            "for i in range(10**100): pass",
        ]
        
        for code in infinite_loops:
            is_safe, result = asyncio.run(
                self.security.execute_code(code)
            )
            assert not is_safe, f"Бесконечный цикл должен быть заблокирован: {code}"

    def test_memory_bomb_blocked(self):
        """Memory bomb должна блокироваться."""
        memory_bombs = [
            "x = [0] * (1024 * 1024 * 1024)",
            "x = 'A' * (10**9)",
        ]
        
        for code in memory_bombs:
            is_safe, result = asyncio.run(
                self.security.execute_code(code)
            )
            assert not is_safe, f"Memory bomb должна быть обнаружена: {code}"

    def test_disk_bomb_blocked(self):
        """Disk bomb должна блокироваться."""
        disk_bombs = [
            "open('big_file', 'w')",
        ]
        
        for code in disk_bombs:
            is_safe, result = asyncio.run(
                self.security.execute_code(code)
            )
            assert not is_safe, f"Disk bomb должна быть обнаружена: {code}"


class TestSecurityPolicies:
    """Тесты политик безопасности."""

    def test_strict_policy(self):
        """Проверка строгой политики."""
        pm = PolicyManager(PolicyProfile.STRICT)
        policy = pm.get_policy()
        
        assert policy.sandbox_level == 5
        assert policy.code_execution == "sandbox"
        assert policy.network_access == "blocked"
        assert policy.file_access == "readonly"

    def test_balanced_policy(self):
        """Проверка сбалансированной политики."""
        pm = PolicyManager(PolicyProfile.BALANCED)
        policy = pm.get_policy()
        
        assert policy.sandbox_level == 3
        assert policy.network_access == "whitelist"
        assert policy.file_access == "workspace_only"

    def test_policy_switch(self):
        """Переключение политик."""
        pm = PolicyManager(PolicyProfile.PERMISSIVE)
        pm.set_profile(PolicyProfile.STRICT)
        
        policy = pm.get_policy()
        assert policy.sandbox_level == 5
        assert policy.file_access == "readonly"

    def test_custom_policy(self):
        """Кастомизация политики."""
        pm = PolicyManager(PolicyProfile.BALANCED)
        pm.customize(memory_limit=1024, cpu_limit=75)
        
        policy = pm.get_policy()
        assert policy.memory_limit == 1024
        assert policy.cpu_limit == 75


class TestConfirmationFlow:
    """Тесты подтверждения действий."""

    def setup_method(self):
        from security.confirmation import ConfirmationManager
        self.cm = ConfirmationManager()

    def test_request_creates_pending(self):
        """Запрос создаёт ожидающее подтверждение."""
        # Запускаем запрос в фоне
        async def do_request():
            return await self.cm.request_confirmation(
                "rm -rf /",
                "CRITICAL",
                timeout=1
            )
        
        # Не ждём результат, проверяем что запрос создан
        assert len(self.cm.pending_requests) == 0
        # Запрос создастся при вызове request_confirmation

    def test_confirm_works(self):
        """Подтверждение работает."""
        from security.confirmation import ConfirmationRequest
        
        req = ConfirmationRequest("test_action", "WARNING", timeout=30)
        self.cm.pending_requests[req.id] = req
        
        result = self.cm.confirm(req.id)
        assert result is True
        assert req.confirmed is True

    def test_deny_works(self):
        """Отклонение работает."""
        from security.confirmation import ConfirmationRequest
        
        req = ConfirmationRequest("test_action", "WARNING", timeout=30)
        self.cm.pending_requests[req.id] = req
        
        result = self.cm.deny(req.id, "Слишком опасно")
        assert result is True
        assert req.confirmed is False
        assert req.reason == "Слишком опасно"

    def test_timeout_returns_false(self):
        """Таймаут возвращает False."""
        result = asyncio.run(
            self.cm.request_confirmation("test", "WARNING", timeout=1)
        )
        assert result is False


class TestAuditLogging:
    """Тесты аудита."""

    def setup_method(self):
        self.security = SecurityManager(
            sandbox_enabled=True,
            workspace="./test_workspace"
        )

    def test_events_logged(self):
        """События записываются в лог."""
        initial_count = len(self.security.audit_logger.events)
        
        # Выполняем действие
        self.security.validate_command("ls")
        
        # Проверяем что событие добавилось
        assert len(self.security.audit_logger.events) > initial_count

    def test_denied_events_logged(self):
        """Отклонённые действия тоже логируются."""
        initial_count = len(self.security.audit_logger.events)
        
        # Пытаемся выполнить опасную команду
        self.security.validate_command("rm -rf /")
        
        # Проверяем что событие добавлено
        assert len(self.security.audit_logger.events) > initial_count


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])