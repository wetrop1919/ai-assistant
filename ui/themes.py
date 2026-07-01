"""
Цветовые схемы и темы для CLI.
"""

import logging
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ThemeName(Enum):
    """Названия тем."""
    DARK = "dark"
    LIGHT = "light"
    CYBERPUNK = "cyberpunk"
    MINIMAL = "minimal"
    MONOKAI = "monokai"


@dataclass
class Theme:
    """Определение темы."""
    name: str
    
    # Основные цвета
    primary: str = "blue"
    secondary: str = "cyan"
    accent: str = "magenta"
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"
    info: str = "blue"
    
    # Фоновые цвета
    bg_primary: str = "black"
    bg_secondary: str = "#1e1e1e"
    
    # Текстовые стили
    header_style: str = "bold cyan"
    code_style: str = "bold yellow on black"
    quote_style: str = "italic cyan"
    
    # Эмодзи
    emoji_success: str = "✅"
    emoji_error: str = "❌"
    emoji_warning: str = "⚠️"
    emoji_info: str = "ℹ️"
    emoji_loading: str = "⏳"
    emoji_brain: str = "🧠"
    emoji_rocket: str = "🚀"
    emoji_thinking: str = "🤔"


# Темы
THEMES: Dict[ThemeName, Theme] = {
    ThemeName.DARK: Theme(
        name="dark",
        primary="bright_blue",
        secondary="bright_cyan",
        accent="bright_magenta",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        header_style="bold bright_cyan",
        code_style="bold bright_yellow on #1e1e1e",
    ),
    ThemeName.LIGHT: Theme(
        name="light",
        primary="blue",
        secondary="cyan",
        accent="magenta",
        success="green",
        warning="orange1",
        error="red",
        bg_primary="white",
        bg_secondary="#f0f0f0",
        header_style="bold blue",
        code_style="bold yellow on #f0f0f0",
    ),
    ThemeName.CYBERPUNK: Theme(
        name="cyberpunk",
        primary="magenta",
        secondary="bright_cyan",
        accent="bright_magenta",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        header_style="bold bright_magenta",
        code_style="bold bright_cyan on black",
        emoji_loading="⚡",
        emoji_brain="💫",
        emoji_thinking="🌀",
    ),
    ThemeName.MINIMAL: Theme(
        name="minimal",
        primary="white",
        secondary="grey",
        accent="bright_white",
        success="white",
        warning="white",
        error="white",
        header_style="bold white",
        code_style="white on black",
    ),
    ThemeName.MONOKAI: Theme(
        name="monokai",
        primary="bright_green",
        secondary="bright_blue",
        accent="bright_magenta",
        success="bright_green",
        warning="bright_yellow",
        error="bright_red",
        header_style="bold bright_green",
        code_style="bright_green on #272822",
    ),
}


class ThemeManager:
    """Менеджер тем."""

    def __init__(self, theme_name: str = "dark"):
        """
        Инициализация менеджера тем.

        Args:
            theme_name: Имя темы
        """
        self.current_theme_name = theme_name
        self.current_theme = self._get_theme(theme_name)
        logger.info(f"🎨 Тема установлена: {theme_name}")

    def _get_theme(self, name: str) -> Theme:
        """Получить тему по имени."""
        try:
            theme_enum = ThemeName(name.lower())
            return THEMES[theme_enum]
        except (ValueError, KeyError):
            logger.warning(f"⚠️ Тема не найдена: {name}, используется dark")
            return THEMES[ThemeName.DARK]

    def set_theme(self, name: str) -> None:
        """Установить тему."""
        self.current_theme = self._get_theme(name)
        self.current_theme_name = name
        logger.info(f"🎨 Тема изменена: {name}")

    def get_color(self, color_type: str) -> str:
        """Получить цвет по типу."""
        return getattr(self.current_theme, color_type, "white")

    def get_available_themes(self) -> list:
        """Получить список доступных тем."""
        return [t.value for t in ThemeName]

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "name": self.current_theme.name,
            "primary": self.current_theme.primary,
            "secondary": self.current_theme.secondary,
            "accent": self.current_theme.accent,
            "success": self.current_theme.success,
            "warning": self.current_theme.warning,
            "error": self.current_theme.error,
        }

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"ThemeManager(theme={self.current_theme_name})"


# Глобальный менеджер тем
_theme_manager: ThemeManager = ThemeManager()


def get_theme_manager() -> ThemeManager:
    """Получить менеджер тем."""
    return _theme_manager