"""
Система навыков AI ассистента.

Навыки - это модули функциональности для расширения ассистента.
"""

from .base import BaseSkill
from .registry import SkillRegistry
from .system import SystemControl
from .files import FileManager
from .web import WebTools
from .automation import Automation
from .coding import CodingHelper

__all__ = [
    "BaseSkill",
    "SkillRegistry",
    "SystemControl",
    "FileManager",
    "WebTools",
    "Automation",
    "CodingHelper",
]