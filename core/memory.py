"""
Система памяти ассистента.

Включает:
- Краткосрочную память (последние 20 сообщений в deque)
- Долговременную память (SQLite база данных)
- Поиск релевантных воспоминаний
- Автоматическое суммирование диалогов
"""

import sqlite3
import logging
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json

from config import config
from utils import retry

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    """Структура одного воспоминания."""

    id: Optional[int] = None
    timestamp: datetime = None
    role: str = ""  # "user" или "assistant"
    content: str = ""
    embedding: Optional[List[float]] = None
    summary: Optional[str] = None

    def __post_init__(self):
        """Инициализация памяти."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """Преобразовать в словарь."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["embedding"] = json.dumps(self.embedding) if self.embedding else None
        return data


class MemoryManager:
    """
    Менеджер памяти ассистента.

    Attributes:
        short_term: Краткосрочная память (deque)
        db_path: Путь к базе данных SQLite
        db_connection: Подключение к БД
    """

    def __init__(self):
        """Инициализация менеджера памяти."""
        self.db_path = config.memory.db_path
        self.short_term_size = config.memory.short_term_size

        # Краткосрочная память - последние сообщения
        self.short_term: deque = deque(maxlen=self.short_term_size)

        # Подключение к БД
        self.db_connection: Optional[sqlite3.Connection] = None

        logger.info("📚 Инициализация MemoryManager")
        self._init_database()

    def _init_database(self) -> None:
        """Инициализировать базу данных SQLite."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.db_connection = sqlite3.connect(self.db_path)
            self.db_connection.row_factory = sqlite3.Row

            cursor = self.db_connection.cursor()

            # Таблица долговременной памяти
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    summary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица для поиска
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_search (
                    memory_id INTEGER PRIMARY KEY,
                    keywords TEXT NOT NULL,
                    FOREIGN KEY(memory_id) REFERENCES memories(id)
                )
            """)

            # Таблица для суммирования диалогов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dialog_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_memory_id INTEGER NOT NULL,
                    end_memory_id INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(start_memory_id) REFERENCES memories(id),
                    FOREIGN KEY(end_memory_id) REFERENCES memories(id)
                )
            """)

            self.db_connection.commit()
            logger.info(f"✅ База данных инициализирована: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise

    def add_short_term(
        self,
        role: str,
        content: str,
    ) -> None:
        """
        Добавить сообщение в краткосрочную память.

        Args:
            role: Роль ("user" или "assistant")
            content: Содержимое сообщения
        """
        memory = Memory(
            timestamp=datetime.now(),
            role=role,
            content=content,
        )
        self.short_term.append(memory)
        logger.debug(f"📝 Добавлено в краткосрочную память: {role}")

    def get_short_term_context(self) -> List[Dict[str, str]]:
        """
        Получить контекст диалога из краткосрочной памяти.

        Returns:
            Список сообщений для Ollama API
        """
        return [
            {
                "role": memory.role,
                "content": memory.content,
            }
            for memory in self.short_term
        ]

    def clear_short_term(self) -> None:
        """Очистить краткосрочную память."""
        self.short_term.clear()
        logger.info("🗑️ Краткосрочная память очищена")

    @retry(max_attempts=3, delay=1.0)
    def add_long_term(
        self,
        role: str,
        content: str,
        keywords: Optional[List[str]] = None,
    ) -> int:
        """
        Добавить сообщение в долговременную память (БД).

        Args:
            role: Роль ("user" или "assistant")
            content: Содержимое сообщения
            keywords: Ключевые слова для поиска

        Returns:
            ID добавленной памяти
        """
        try:
            cursor = self.db_connection.cursor()

            # Добавляем в основную таблицу
            cursor.execute(
                """
                INSERT INTO memories (role, content)
                VALUES (?, ?)
                """,
                (role, content),
            )

            memory_id = cursor.lastrowid

            # Добавляем ключевые слова для поиска
            if keywords:
                keywords_str = ",".join(keywords)
                cursor.execute(
                    """
                    INSERT INTO memory_search (memory_id, keywords)
                    VALUES (?, ?)
                    """,
                    (memory_id, keywords_str),
                )

            self.db_connection.commit()
            logger.debug(f"💾 Добавлено в долговременную память: {role}")
            return memory_id

        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка добавления в долговременную память: {e}")
            raise

    def search_memories(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Memory]:
        """
        Поиск релевантных воспоминаний по ключевым словам.

        Args:
            query: Поисковый запрос
            limit: Максимум результатов

        Returns:
            Список найденных воспоминаний
        """
        try:
            cursor = self.db_connection.cursor()

            # Простой поиск по ключевым словам и содержимому
            query_lower = query.lower()

            cursor.execute(
                """
                SELECT id, timestamp, role, content, embedding, summary
                FROM memories
                WHERE content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (f"%{query_lower}%", limit),
            )

            rows = cursor.fetchall()
            memories = []

            for row in rows:
                memory = Memory(
                    id=row["id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    role=row["role"],
                    content=row["content"],
                    embedding=(
                        json.loads(row["embedding"])
                        if row["embedding"]
                        else None
                    ),
                    summary=row["summary"],
                )
                memories.append(memory)

            logger.debug(f"🔍 Найдено {len(memories)} воспоминаний по запросу")
            return memories

        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка поиска в памяти: {e}")
            return []

    def get_recent_memories(
        self,
        limit: int = 10,
    ) -> List[Memory]:
        """
        Получить недавние воспоминания.

        Args:
            limit: Максимум воспоминаний

        Returns:
            Список недавних воспоминаний
        """
        try:
            cursor = self.db_connection.cursor()

            cursor.execute(
                """
                SELECT id, timestamp, role, content, embedding, summary
                FROM memories
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()
            memories = []

            for row in rows:
                memory = Memory(
                    id=row["id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    role=row["role"],
                    content=row["content"],
                    embedding=(
                        json.loads(row["embedding"])
                        if row["embedding"]
                        else None
                    ),
                    summary=row["summary"],
                )
                memories.append(memory)

            return memories

        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка получения недавних воспоминаний: {e}")
            return []

    def get_memory_stats(self) -> Dict:
        """
        Получить статистику памяти.

        Returns:
            Словарь со статистикой
        """
        try:
            cursor = self.db_connection.cursor()

            cursor.execute("SELECT COUNT(*) as total FROM memories")
            total = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) as user FROM memories WHERE role = 'user'"
            )
            user_count = cursor.fetchone()["user"]

            cursor.execute(
                "SELECT COUNT(*) as assistant FROM memories WHERE role = 'assistant'"
            )
            assistant_count = cursor.fetchone()["assistant"]

            stats = {
                "total_memories": total,
                "user_messages": user_count,
                "assistant_messages": assistant_count,
                "short_term_size": len(self.short_term),
                "short_term_max": self.short_term_size,
            }

            return stats

        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}

    def save_dialog_summary(
        self,
        start_memory_id: int,
        end_memory_id: int,
        summary: str,
    ) -> int:
        """
        Сохранить суммирование диалога.

        Args:
            start_memory_id: ID начального воспоминания
            end_memory_id: ID конечного воспоминания
            summary: Текст суммирования

        Returns:
            ID суммирования
        """
        try:
            cursor = self.db_connection.cursor()

            cursor.execute(
                """
                INSERT INTO dialog_summaries
                (start_memory_id, end_memory_id, summary)
                VALUES (?, ?, ?)
                """,
                (start_memory_id, end_memory_id, summary),
            )

            self.db_connection.commit()
            summary_id = cursor.lastrowid

            logger.info(f"📊 Суммирование диалога сохранено (ID: {summary_id})")
            return summary_id

        except sqlite3.Error as e:
            logger.error(f"❌ Ошибка сохранения суммирования: {e}")
            raise

    def export_memories(
        self,
        output_file: str = "memories_export.json",
    ) -> None:
        """
        Экспортировать все воспоминания в JSON.

        Args:
            output_file: Путь к файлу экспорта
        """
        try:
            memories = self.get_recent_memories(limit=10000)

            data = {
                "exported_at": datetime.now().isoformat(),
                "total_memories": len(memories),
                "memories": [
                    {
                        "id": m.id,
                        "timestamp": m.timestamp.isoformat(),
                        "role": m.role,
                        "content": m.content,
                    }
                    for m in memories
                ],
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Воспоминания экспортированы в {output_file}")

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта воспоминаний: {e}")
            raise

    def close(self) -> None:
        """Закрыть подключение к БД."""
        if self.db_connection:
            self.db_connection.close()
            logger.info("✅ Подключение к БД закрыто")

    def __repr__(self) -> str:
        """Строковое представление объекта."""
        return (
            f"MemoryManager(short_term={len(self.short_term)}, "
            f"db_path={self.db_path})"
        )
