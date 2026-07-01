"""
Система восстановления и откатов.
"""

import logging
import shutil
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class RecoveryPoint:
    """Точка восстановления."""

    def __init__(self, name: str, timestamp: str, files: Dict[str, str]):
        """
        Инициализация.

        Args:
            name: Имя точки восстановления
            timestamp: Временная метка
            files: Словарь файлов и их хешей
        """
        self.name = name
        self.timestamp = timestamp
        self.files = files
        self.created_at = datetime.now().isoformat()


class RecoveryManager:
    """Менеджер восстановления."""

    def __init__(self, backup_dir: str = ".recovery"):
        """
        Инициализация.

        Args:
            backup_dir: Директория для бэкапов
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.recovery_points: Dict[str, RecoveryPoint] = {}

        logger.info(f"🔄 RecoveryManager инициализирован ({backup_dir})")

    def create_recovery_point(
        self,
        name: str,
        files_to_backup: List[str],
    ) -> str:
        """
        Создать точку восстановления.

        Args:
            name: Имя точки
            files_to_backup: Список файлов для бэкапа

        Returns:
            ID точки восстановления
        """
        try:
            timestamp = datetime.now().isoformat()
            point_dir = self.backup_dir / name
            point_dir.mkdir(parents=True, exist_ok=True)

            files_info = {}

            for file_path in files_to_backup:
                try:
                    file = Path(file_path)
                    if file.exists():
                        # Копируем файл
                        backup_file = point_dir / file.name
                        shutil.copy2(file, backup_file)

                        # Сохраняем хеш
                        import hashlib

                        with open(file, "rb") as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                            files_info[file_path] = file_hash

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка бэкапа файла {file_path}: {e}")

            # Сохраняем информацию о точке
            point = RecoveryPoint(name, timestamp, files_info)
            self.recovery_points[name] = point

            logger.info(f"✅ Точка восстановления создана: {name}")
            return name

        except Exception as e:
            logger.error(f"❌ Ошибка создания точки восстановления: {e}")
            return ""

    def restore_from_point(self, point_name: str) -> bool:
        """
        Восстановить из точки.

        Args:
            point_name: Имя точки восстановления

        Returns:
            True если успешно
        """
        try:
            if point_name not in self.recovery_points:
                logger.warning(f"⚠️ Точка восстановления не найдена: {point_name}")
                return False

            point = self.recovery_points[point_name]
            point_dir = self.backup_dir / point_name

            for original_file, file_hash in point.files.items():
                try:
                    backup_file = point_dir / Path(original_file).name

                    if backup_file.exists():
                        shutil.copy2(backup_file, original_file)
                        logger.info(f"✅ Файл восстановлен: {original_file}")

                except Exception as e:
                    logger.warning(f"⚠️ Ошибка восстановления {original_file}: {e}")

            logger.info(f"✅ Восстановление завершено: {point_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка восстановления: {e}")
            return False

    def list_recovery_points(self) -> List[str]:
        """Получить список точек восстановления."""
        return list(self.recovery_points.keys())

    def delete_recovery_point(self, point_name: str) -> bool:
        """
        Удалить точку восстановления.

        Args:
            point_name: Имя точки

        Returns:
            True если успешно
        """
        try:
            if point_name in self.recovery_points:
                point_dir = self.backup_dir / point_name
                shutil.rmtree(point_dir)
                del self.recovery_points[point_name]
                logger.info(f"✅ Точка восстановления удалена: {point_name}")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Ошибка удаления точки восстановления: {e}")
            return False

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"RecoveryManager(points={len(self.recovery_points)})"