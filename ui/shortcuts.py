"""
Горячие клавиши и быстрые команды.
"""

import logging
from typing import Dict, Callable, Optional
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class Shortcut:
    """Определение горячей клавиши."""
    key: str
    description: str
    handler: Callable
    mode: str = "global"  # global, editor, search


class ShortcutManager:
    """Менеджер горячих клавиш."""

    def __init__(self):
        """Инициализация."""
        self.shortcuts: Dict[str, Shortcut] = {}
        self._register_default_shortcuts()

    def _register_default_shortcuts(self) -> None:
        """Зарегистрировать стандартные горячие клавиши."""
        self.register(
            "ctrl-l",
            "Очистить экран",
            self._clear_screen,
        )

        self.register(
            "ctrl-s",
            "Сохранить диалог",
            self._save_dialog,
        )

        self.register(
            "ctrl-c",
            "Прервать операцию",
            self._interrupt,
        )

        self.register(
            "ctrl-d",
            "Выход",
            self._exit,
        )

        self.register(
            "alt-v",
            "Переключить голос",
            self._toggle_voice,
        )

        self.register(
            "alt-m",
            "Сменить модель",
            self._change_model,
        )

        self.register(
            "alt-t",
            "Сменить тему",
            self._change_theme,
        )

        logger.info("✅ Стандартные горячие клавиши зарегистрированы")

    def register(
        self,
        key: str,
        description: str,
        handler: Callable,
        mode: str = "global",
    ) -> None:
        """
        Зарегистрировать горячую клавишу.

        Args:
            key: Комбинация клавиш
            description: Описание
            handler: Функция обработчик
            mode: Режим
        """
        shortcut = Shortcut(key, description, handler, mode)
        self.shortcuts[key] = shortcut
        logger.debug(f"✅ Горячая клавиша зарегистрирована: {key}")

    def unregister(self, key: str) -> bool:
        """
        Отменить регистрацию горячей клавиши.

        Args:
            key: Комбинация клавиш

        Returns:
            True если успешно
        """
        if key in self.shortcuts:
            del self.shortcuts[key]
            logger.debug(f"✅ Горячая клавиша удалена: {key}")
            return True
        return False

    async def handle(self, key: str) -> bool:
        """
        Обработать нажатие горячей клавиши.

        Args:
            key: Комбинация клавиш

        Returns:
            True если обработана
        """
        if key in self.shortcuts:
            shortcut = self.shortcuts[key]
            try:
                if asyncio.iscoroutinefunction(shortcut.handler):
                    await shortcut.handler()
                else:
                    shortcut.handler()

                logger.debug(f"✅ Горячая клавиша обработана: {key}")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка обработки горячей клавиши: {e}")
                return False

        return False

    def get_shortcuts(self, mode: Optional[str] = None) -> Dict[str, Shortcut]:
        """
        Получить горячие клавиши.

        Args:
            mode: Режим фильтрации

        Returns:
            Словарь горячих клавиш
        """
        if mode:
            return {k: v for k, v in self.shortcuts.items() if v.mode == mode}
        return self.shortcuts.copy()

    # Обработчики по умолчанию

    async def _clear_screen(self) -> None:
        """Очистить экран."""
        import os
        os.system("cls" if os.name == "nt" else "clear")
        logger.info("✅ Экран очищен")

    async def _save_dialog(self) -> None:
        """Сохранить диалог."""
        logger.info("💾 Сохранение диалога...")

    async def _interrupt(self) -> None:
        """Прервать операцию."""
        logger.info("⏹️ Операция прервана")

    async def _exit(self) -> None:
        """Выход."""
        logger.info("👋 Выход")

    async def _toggle_voice(self) -> None:
        """Переключить голос."""
        logger.info("🔊 Голосовой режим переключен")

    async def _change_model(self) -> None:
        """Сменить модель."""
        logger.info("🔄 Смена модели...")

    async def _change_theme(self) -> None:
        """Сменить тему."""
        logger.info("🎨 Смена темы...")

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"ShortcutManager(shortcuts={len(self.shortcuts)})"


# Глобальный менеджер
_shortcut_manager = ShortcutManager()


def get_shortcut_manager() -> ShortcutManager:
    """Получить менеджер горячих клавиш."""
    return _shortcut_manager