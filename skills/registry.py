"""
Реестр навыков с автообнаружением и маршрутизацией.

Управляет регистрацией, приоритетами и маршрутизацией запросов.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import importlib
import inspect

from .base import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Реестр навыков.

    Attributes:
        skills: Список зарегистрированных навыков
    """

    def __init__(self, brain=None, memory=None):
        """
        Инициализация реестра навыков.

        Args:
            brain: Ссылка на мозг ассистента
            memory: Ссылка на систему памяти
        """
        self.skills: List[BaseSkill] = []
        self.brain = brain
        self.memory = memory

        logger.info("🎯 Инициализация SkillRegistry")
        self._register_builtin_skills()

    def _register_builtin_skills(self) -> None:
        """Зарегистрировать встроенные навыки."""
        builtin_skills_classes = [
            ("system", "SystemControl"),
            ("files", "FileManager"),
            ("web", "WebTools"),
            ("automation", "Automation"),
            ("coding", "CodingHelper"),
        ]

        for module_name, class_name in builtin_skills_classes:
            try:
                module = importlib.import_module(f"skills.{module_name}")
                skill_class = getattr(module, class_name)
                skill = skill_class(
                    brain=self.brain,
                    memory=self.memory,
                )
                self.register(skill)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить {class_name}: {e}")

        logger.info(f"✅ Зарегистрировано {len(self.skills)} навыков")

    def register(self, skill: BaseSkill) -> None:
        """
        Зарегистрировать навык.

        Args:
            skill: Объект навыка

        Raises:
            ValueError: Если навык с таким именем уже зарегистрирован
        """
        if any(s.name == skill.name for s in self.skills):
            raise ValueError(f"Навык с именем '{skill.name}' уже зарегистрирован")

        self.skills.append(skill)
        # Сортируем по приоритету (выше приоритет = в начале)
        self.skills.sort(key=lambda s: s.priority, reverse=True)
        logger.info(f"✅ Навык зарегистрирован: {skill.name} (приоритет: {skill.priority})")

    def unregister(self, skill_name: str) -> bool:
        """
        Отменить регистрацию навыка.

        Args:
            skill_name: Имя навыка

        Returns:
            True если навык был удален
        """
        for i, skill in enumerate(self.skills):
            if skill.name == skill_name:
                self.skills.pop(i)
                logger.info(f"✅ Навык отменен: {skill_name}")
                return True

        logger.warning(f"⚠️ Навык не найден: {skill_name}")
        return False

    def find_skill(self, prompt: str) -> Optional[BaseSkill]:
        """
        Найти подходящий навык для обработки запроса по приоритету.

        Args:
            prompt: Текст запроса

        Returns:
            Навык если найден, иначе None
        """
        for skill in self.skills:  # Уже отсортированы по приоритету
            if skill.is_enabled and skill.can_handle(prompt):
                logger.debug(f"🎯 Найден подходящий навык: {skill.name}")
                return skill

        logger.debug("ℹ️ Подходящий навык не найден")
        return None

    async def execute_skill(self, prompt: str) -> Optional[str]:
        """
        Найти и выполнить подходящий навык.

        Args:
            prompt: Текст запроса

        Returns:
            Результат выполнения навыка
        """
        skill = self.find_skill(prompt)

        if skill is None:
            logger.debug("ℹ️ Подходящий навык не найден, используем основной мозг")
            return None

        try:
            result = await skill.execute(prompt)
            logger.debug(f"✅ Навык выполнен: {skill.name}")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения навыка {skill.name}: {e}")
            return None

    def get_all_skills(self) -> List[Dict[str, Any]]:
        """
        Получить информацию о всех навыках.

        Returns:
            Список информации о навыках
        """
        return [skill.get_info() for skill in self.skills]

    def get_skill_by_name(self, skill_name: str) -> Optional[BaseSkill]:
        """
        Получить навык по имени.

        Args:
            skill_name: Имя навыка

        Returns:
            Навык если найден
        """
        for skill in self.skills:
            if skill.name == skill_name:
                return skill
        return None

    def enable_skill(self, skill_name: str) -> bool:
        """
        Включить навык.

        Args:
            skill_name: Имя навыка

        Returns:
            True если успешно
        """
        skill = self.get_skill_by_name(skill_name)
        if skill:
            skill.is_enabled = True
            logger.info(f"✅ Навык включен: {skill_name}")
            return True
        return False

    def disable_skill(self, skill_name: str) -> bool:
        """
        Отключить навык.

        Args:
            skill_name: Имя навыка

        Returns:
            True если успешно
        """
        skill = self.get_skill_by_name(skill_name)
        if skill:
            skill.is_enabled = False
            logger.info(f"✅ Навык отключен: {skill_name}")
            return True
        return False

    def get_skill_actions(self, skill_name: str) -> List[Dict[str, Any]]:
        """
        Получить логи действий навыка.

        Args:
            skill_name: Имя навыка

        Returns:
            Список логов действий
        """
        skill = self.get_skill_by_name(skill_name)
        if skill:
            return skill.get_action_log()
        return []

    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return f"SkillRegistry(skills={len(self.skills)})"
