"""
Тесты системы безопасности.
"""

import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from core.security import (
    SandboxDetector,
    CodeSandbox,
    CommandValidator,
    FSMonitor,
    AuditLogger,
    SecurityManager,
    DangerLevel,
)
from security.policies import PolicyManager, PolicyProfile
from security.confirmation import ConfirmationManager
from security.recovery import RecoveryManager


class TestSandboxDetector:
    """Тесты детектора песочницы."""

    def test_detection(self):
        """Тест обнаружения окружения."""
        detector = SandboxDetector()
        info = detector.get_info()

        assert "isolation_level" in info
        assert "detected_env" in info
        assert info["isolation_value"] >= 1


class TestCodeSandbox:
    """Тесты песочницы для кода."""

    @pytest.mark.asyncio
    async def test_safe_code(self):
        """Тест безопасного кода."""
        sandbox = CodeSandbox()
        success, result = await sandbox.execute("x = 5 + 3\nresult = x")
        assert success

    @pytest.mark.asyncio
    async def test_dangerous_code(self):
        """Тест опасного кода."""
        sandbox = CodeSandbox()
        success, result = await sandbox.execute("import os\nos.system('ls')")
        assert not success


class TestCommandValidator:
    """Тесты валидатора команд."""

    def test_safe_command(self):
        """Тест безопасной команды."""
        validator = CommandValidator()
        valid, level, reason = validator.validate("ls -la")
        assert valid
        assert level == DangerLevel.SAFE

    def test_dangerous_command(self):
        """Тест опасной команды."""
        validator = CommandValidator()
        valid, level, reason = validator.validate("rm -rf /")
        assert not valid


class TestFSMonitor:
    """Тесты монитора файловой системы."""

    def test_protected_dirs(self, tmp_path):
        """Тест защищённых директорий."""
        monitor = FSMonitor(str(tmp_path))
        assert not monitor.can_write("/etc/passwd")
        assert not monitor.can_write("/bin/ls")


class TestPolicyManager:
    """Тесты менеджера политик."""

    def test_policy_profiles(self):
        """Тест профилей политик."""
        for profile in PolicyProfile:
            manager = PolicyManager(profile)
            policy = manager.get_policy()
            assert policy.name == profile.value


class TestConfirmationManager:
    """Тесты менеджера подтверждений."""

    @pytest.mark.asyncio
    async def test_confirmation(self):
        """Тест подтверждения."""
        manager = ConfirmationManager()
        requests = manager.get_pending_requests()
        assert isinstance(requests, dict)


class TestRecoveryManager:
    """Тесты менеджера восстановления."""

    def test_recovery_points(self, tmp_path):
        """Тест точек восстановления."""
        manager = RecoveryManager(str(tmp_path))
        points = manager.list_recovery_points()
        assert isinstance(points, list)


class TestSecurityManager:
    """Тесты менеджера безопасности."""

    def test_initialization(self):
        """Тест инициализации."""
        manager = SecurityManager()
        assert manager is not None
        assert manager.sandbox_detector is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])