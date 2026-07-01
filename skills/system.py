"""
Навык управления системой.

Возможности:
- Информация о системе (CPU, RAM, диск)
- Управление процессами
- Запуск приложений
- Управление громкостью
- Скриншоты
- Планировщик задач
- Мониторинг ресурсов
"""

import logging
import subprocess
import os
import platform
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .base import BaseSkill

logger = logging.getLogger(__name__)


class SystemControl(BaseSkill):
    """Управление системой."""

    def __init__(self, brain=None, memory=None):
        """Инициализация навыка управления системой."""
        super().__init__(
            name="system_control",
            description="Управление системой, процессами и ресурсами",
            version="1.0.0",
            priority=60,
            brain=brain,
            memory=memory,
        )
        self.system = platform.system()
        self.monitored_processes: Dict[int, Dict[str, Any]] = {}
        self.scheduled_tasks: List[Dict[str, Any]] = []

    def can_handle(self, prompt: str) -> bool:
        """Проверить, может ли обработать запрос."""
        keywords = [
            "система", "процесс", "запусти", "приложение",
            "громкость", "скриншот", "память", "cpu", "диск",
            "запланировать", "задача", "мониторинг",
        ]
        return any(kw in prompt.lower() for kw in keywords)

    def get_capabilities(self) -> List[str]:
        """Получить список возможностей."""
        return [
            "get_system_info - информация о системе",
            "execute_command - выполнение команд",
            "manage_process - управление процессами",
            "open_application - запуск приложений",
            "control_volume - управление громкостью",
            "take_screenshot - скриншот экрана",
            "get_clipboard - получить буфер обмена",
            "set_clipboard - установить буфер обмена",
            "schedule_task - запланировать задачу",
            "monitor_resources - мониторинг ресурсов",
        ]

    async def execute(self, prompt: str) -> str:
        """Выполнить команду управления системой."""
        try:
            prompt_lower = prompt.lower()

            if "информация" in prompt_lower or "систем" in prompt_lower:
                return await self._get_system_info()

            elif "процесс" in prompt_lower or "запусти" in prompt_lower:
                return await self._handle_process_command(prompt)

            elif "громкость" in prompt_lower:
                return await self._handle_volume_command(prompt)

            elif "скриншот" in prompt_lower:
                return await self._take_screenshot()

            elif "буфер" in prompt_lower or "clipboard" in prompt_lower:
                return await self._handle_clipboard_command(prompt)

            elif "запланировать" in prompt_lower or "задача" in prompt_lower:
                return await self._handle_schedule_command(prompt)

            else:
                return "🤖 Команда управления системой не распознана"

        except Exception as e:
            self.log_action(
                "execute",
                status="error",
                details={"error": str(e)},
                level="ERROR",
            )
            return f"❌ Ошибка: {e}"

    async def _get_system_info(self) -> str:
        """Получить информацию о системе."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            boot_time = datetime.fromtimestamp(
                psutil.boot_time()
            ).strftime("%Y-%m-%d %H:%M:%S")

            info = f"""
📊 Информация о системе:

🖥️  ОС: {self.system} {platform.release()}
⚙️  Процессор: {platform.processor()}
📈 CPU: {cpu_percent}%
💾 Память: {memory.percent}% ({memory.used // (1024**3)} GB / {memory.total // (1024**3)} GB)
💿 Диск: {disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)
🔄 Uptime: {boot_time}
"""
            self.log_action(
                "get_system_info",
                status="success",
                details={"cpu": cpu_percent, "memory": memory.percent},
            )
            return info

        except ImportError:
            return "⚠️ Требуется psutil: pip install psutil"
        except Exception as e:
            return f"❌ Ошибка получения информации: {e}"

    async def _handle_process_command(self, prompt: str) -> str:
        """Обработать команду управления процессом."""
        try:
            import psutil

            if "список" in prompt.lower() or "все процессы" in prompt.lower():
                processes = []
                for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
                    processes.append(
                        f"  {proc.info['name']} (PID: {proc.info['pid']}, "
                        f"CPU: {proc.info['cpu_percent']}%)"
                    )

                return "📋 Активные процессы:\n" + "\n".join(processes[:10])

            else:
                return "ℹ️ Команда процесса не распознана"

        except Exception as e:
            return f"❌ Ошибка управления процессом: {e}"

    async def _handle_volume_command(self, prompt: str) -> str:
        """Обработать команду управления громкостью."""
        if self.sandbox_mode:
            self.log_action(
                "control_volume",
                status="simulated",
                details={"prompt": prompt},
            )
            return "🔒 [SIMULATED] Громкость система установлена"

        return "⚠️ Управление громкостью требует системных прав"

    async def _take_screenshot(self) -> str:
        """Сделать скриншот экрана."""
        if self.sandbox_mode:
            self.log_action(
                "take_screenshot",
                status="simulated",
            )
            return "🔒 [SIMULATED] Скриншот сохранён: screenshot_2024_01_15.png"

        try:
            from PIL import ImageGrab
            import tempfile

            screenshot = ImageGrab.grab()
            temp_path = tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False,
            ).name
            screenshot.save(temp_path)

            self.log_action(
                "take_screenshot",
                status="success",
                details={"path": temp_path},
            )
            return f"✅ Скриншот сохранён: {temp_path}"

        except ImportError:
            return "⚠️ Требуется Pillow: pip install Pillow"
        except Exception as e:
            return f"❌ Ошибка скриншота: {e}"

    async def _handle_clipboard_command(self, prompt: str) -> str:
        """Обработать команду буфера обмена."""
        try:
            import pyperclip

            if "получить" in prompt.lower():
                text = pyperclip.paste()
                self.log_action(
                    "get_clipboard",
                    status="success",
                    details={"length": len(text)},
                )
                return f"📋 Содержимое буфера обмена:\n{text[:500]}"

            elif "установить" in prompt.lower():
                if self.sandbox_mode:
                    self.log_action(
                        "set_clipboard",
                        status="simulated",
                    )
                    return "🔒 [SIMULATED] Текст скопирован в буфер обмена"

                return "ℹ️ Установить текст в буфер обмена"

            else:
                return "ℹ️ Команда буфера обмена не распознана"

        except ImportError:
            return "⚠️ Требуется pyperclip: pip install pyperclip"
        except Exception as e:
            return f"❌ Ошибка буфера обмена: {e}"

    async def _handle_schedule_command(self, prompt: str) -> str:
        """Обработать команду планировщика задач."""
        task = {
            "id": len(self.scheduled_tasks) + 1,
            "command": prompt,
            "created_at": datetime.now().isoformat(),
            "status": "scheduled",
        }

        self.scheduled_tasks.append(task)

        self.log_action(
            "schedule_task",
            status="simulated" if self.sandbox_mode else "success",
            details={"task_id": task["id"]},
        )

        return (
            f"📅 Задача запланирована (ID: {task['id']})\n"
            f"Команда: {prompt}"
        )

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"SystemControl(scheduled_tasks={len(self.scheduled_tasks)})"
