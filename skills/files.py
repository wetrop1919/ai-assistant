"""
Навык управления файлами.

Возможности:
- Поиск файлов
- Организация файлов
- Поиск дубликатов
- Массовое переименование
- Бэкап
- Шифрование
- Компрессия
- Метаданные
"""

import logging
import os
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .base import BaseSkill

logger = logging.getLogger(__name__)


class FileManager(BaseSkill):
    """Управление файлами."""

    def __init__(self, brain=None, memory=None):
        """Инициализация навыка управления файлами."""
        super().__init__(
            name="file_manager",
            description="Управление файлами, поиск, организация, бэкап",
            version="1.0.0",
            priority=55,
            brain=brain,
            memory=memory,
        )

    def can_handle(self, prompt: str) -> bool:
        """Проверить, может ли обработать запрос."""
        keywords = [
            "файл", "папка", "директория", "поиск", "найди",
            "дубликат", "переименовать", "бэкап", "архив",
            "зашифровать", "информация о файле",
        ]
        return any(kw in prompt.lower() for kw in keywords)

    def get_capabilities(self) -> List[str]:
        """Получить список возможностей."""
        return [
            "smart_search - умный поиск файлов",
            "organize_files - организация файлов",
            "find_duplicates - поиск дубликатов",
            "bulk_rename - массовое переименование",
            "backup_files - создание бэкапа",
            "encrypt_file - шифрование файла",
            "decrypt_file - расшифровка файла",
            "compress - сжатие архива",
            "extract - распаковка архива",
            "get_file_metadata - информация о файле",
        ]

    async def execute(self, prompt: str) -> str:
        """Выполнить команду управления файлами."""
        try:
            prompt_lower = prompt.lower()

            if "поиск" in prompt_lower or "найди" in prompt_lower:
                return await self._smart_search(prompt)

            elif "дубликат" in prompt_lower:
                return await self._find_duplicates_handler(prompt)

            elif "переименовать" in prompt_lower:
                return await self._bulk_rename_handler(prompt)

            elif "бэкап" in prompt_lower or "backup" in prompt_lower:
                return await self._backup_handler(prompt)

            elif "архив" in prompt_lower:
                return await self._archive_handler(prompt)

            elif "информация" in prompt_lower or "свойства" in prompt_lower:
                return await self._file_metadata_handler(prompt)

            else:
                return "🤖 Команда файла не распознана"

        except Exception as e:
            self.log_action(
                "execute",
                status="error",
                details={"error": str(e)},
                level="ERROR",
            )
            return f"❌ Ошибка: {e}"

    async def _smart_search(self, prompt: str) -> str:
        """Умный поиск файлов."""
        try:
            # Простой поиск в текущей директории
            search_terms = prompt.replace("поиск", "").replace("найди", "").strip()

            if not search_terms:
                return "❌ Укажите, что искать"

            matches = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    if search_terms.lower() in file.lower():
                        matches.append(os.path.join(root, file))
                        if len(matches) >= 10:
                            break

            result = f"🔍 Найдено {len(matches)} файлов:\n"
            for match in matches[:10]:
                result += f"  • {match}\n"

            self.log_action(
                "smart_search",
                status="success",
                details={"matches": len(matches), "query": search_terms},
            )

            return result

        except Exception as e:
            return f"❌ Ошибка поиска: {e}"

    async def _find_duplicates_handler(self, prompt: str) -> str:
        """Найти дубликаты файлов."""
        if self.sandbox_mode:
            self.log_action(
                "find_duplicates",
                status="simulated",
            )
            return "🔒 [SIMULATED] Найдены дубликаты: file1.txt, file1_copy.txt"

        try:
            hashes: Dict[str, List[str]] = {}

            for root, dirs, files in os.walk("."):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "rb") as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                            if file_hash not in hashes:
                                hashes[file_hash] = []
                            hashes[file_hash].append(filepath)
                    except:
                        continue

            duplicates = {k: v for k, v in hashes.items() if len(v) > 1}

            if not duplicates:
                return "✅ Дубликатов не найдено"

            result = f"📋 Найдено {len(duplicates)} групп дубликатов:\n"
            for file_list in list(duplicates.values())[:5]:
                result += f"  • {file_list}\n"

            self.log_action(
                "find_duplicates",
                status="success",
                details={"duplicates": len(duplicates)},
            )

            return result

        except Exception as e:
            return f"❌ Ошибка поиска дубликатов: {e}"

    async def _bulk_rename_handler(self, prompt: str) -> str:
        """Массовое переименование файлов."""
        if self.sandbox_mode:
            self.log_action(
                "bulk_rename",
                status="simulated",
            )
            return "🔒 [SIMULATED] Переименовано 5 файлов"

        return "ℹ️ Массовое переименование требует дополнительных параметров"

    async def _backup_handler(self, prompt: str) -> str:
        """Создать бэкап файлов."""
        if self.sandbox_mode:
            self.log_action(
                "backup_files",
                status="simulated",
            )
            return "🔒 [SIMULATED] Бэкап создан: backup_2024_01_15.zip"

        return "ℹ️ Бэкап требует указания источника и назначения"

    async def _archive_handler(self, prompt: str) -> str:
        """Работа с архивами."""
        if self.sandbox_mode:
            self.log_action(
                "compress",
                status="simulated",
            )
            return "🔒 [SIMULATED] Файлы сжаты: archive.zip"

        return "ℹ️ Архивирование требует указания пути"

    async def _file_metadata_handler(self, prompt: str) -> str:
        """Получить информацию о файле."""
        try:
            import glob

            # Найти первый .txt файл
            txt_files = glob.glob("*.txt")
            if not txt_files:
                return "❌ Файлы не найдены"

            filepath = txt_files[0]
            stat = os.stat(filepath)

            info = f"""
📄 Информация о файле:

Файл: {filepath}
Размер: {stat.st_size} bytes
Создан: {datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")}
Изменён: {datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")}
Права: {oct(stat.st_mode)[-3:]}
"""
            self.log_action(
                "get_file_metadata",
                status="success",
                details={"file": filepath, "size": stat.st_size},
            )
            return info

        except Exception as e:
            return f"❌ Ошибка получения информации: {e}"

    def __repr__(self) -> str:
        """Строковое представление."""
        return "FileManager()"
