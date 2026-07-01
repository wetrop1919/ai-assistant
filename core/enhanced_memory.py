"""
Расширенная система памяти с episodic, semantic и procedural памятью.

Использует ChromaDB + SQLite + NetworkX.
"""

import logging
import sqlite3
import json
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

try:
    import networkx as nx
except ImportError:
    nx = None


class EnhancedMemory:
    """
    Расширенная система памяти.

    Включает:
    - Episodic memory: события с временными метками
    - Semantic memory: факты и знания
    - Procedural memory: как что-то делать
    - Working memory: текущий контекст
    """

    def __init__(
        self,
        db_path: str = "memory.db",
        rag_system=None,
        max_working_memory: int = 50,
    ):
        """
        Инициализация расширенной памяти.

        Args:
            db_path: Путь к БД
            rag_system: Система RAG (опционально)
            max_working_memory: Размер рабочей памяти
        """
        self.db_path = db_path
        self.rag_system = rag_system
        self.max_working_memory = max_working_memory

        # Краткосрочная память
        self.short_term: deque = deque(maxlen=20)
        self.working_memory: deque = deque(maxlen=max_working_memory)

        # Граф знаний
        self.knowledge_graph = nx.DiGraph() if nx else None

        # Статистика
        self.access_counts: Dict[str, int] = {}
        self.last_access: Dict[str, datetime] = {}

        logger.info("💾 Инициализация EnhancedMemory")
        self._init_database()

    def _init_database(self) -> None:
        """Инициализировать расширенную схему БД."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Episodic Memory - события
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT,
                    emotional_valence REAL DEFAULT 0.0,
                    importance REAL DEFAULT 0.5,
                    related_events TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    accessed_at DATETIME
                )
            """)

            # Semantic Memory - факты
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semantic_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT NOT NULL,
                    confidence REAL DEFAULT 0.8,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Procedural Memory - процедуры
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS procedural_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    procedure_name TEXT UNIQUE NOT NULL,
                    steps TEXT NOT NULL,
                    prerequisites TEXT,
                    success_rate REAL DEFAULT 0.0,
                    last_used DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Сущности - для графа знаний
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    entity_type TEXT NOT NULL,
                    properties TEXT,
                    frequency INTEGER DEFAULT 1
                )
            """)

            # Связи между сущностями
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_entity_id INTEGER NOT NULL,
                    target_entity_id INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    FOREIGN KEY(source_entity_id) REFERENCES entities(id),
                    FOREIGN KEY(target_entity_id) REFERENCES entities(id)
                )
            """)

            conn.commit()
            conn.close()
            logger.info("✅ Расширенная схема БД инициализирована")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise

    def add_episodic_memory(
        self,
        event_type: str,
        content: str,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
    ) -> int:
        """
        Добавить episodic memory (событие).

        Args:
            event_type: Тип события
            content: Содержимое события
            importance: Важность (0-1)
            emotional_valence: Эмоциональная окраска (-1 до 1)

        Returns:
            ID события
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO episodic_memories
                (event_type, content, importance, emotional_valence)
                VALUES (?, ?, ?, ?)
            """, (event_type, content, importance, emotional_valence))

            memory_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Добавляем в RAG если доступна
            if self.rag_system:
                self.rag_system.add_memory(
                    content,
                    memory_type="episodic",
                    importance=importance,
                )

            logger.debug(f"📝 Episodic memory добавлено: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"❌ Ошибка добавления episodic memory: {e}")
            return -1

    def add_semantic_memory(
        self,
        key: str,
        value: str,
        category: str,
        confidence: float = 0.8,
    ) -> bool:
        """
        Добавить semantic memory (факт).

        Args:
            key: Ключ факта
            value: Значение факта
            category: Категория (user_info, system, preferences)
            confidence: Уверенность (0-1)

        Returns:
            True если успешно
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO semantic_memories
                (key, value, category, confidence)
                VALUES (?, ?, ?, ?)
            """, (key, value, category, confidence))

            conn.commit()
            conn.close()

            # Обновляем граф знаний
            if self.knowledge_graph:
                self._update_knowledge_graph(key, value, category)

            logger.debug(f"🧠 Semantic memory добавлено: {key}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка добавления semantic memory: {e}")
            return False

    def get_semantic_memory(self, key: str) -> Optional[str]:
        """
        Получить semantic memory.

        Args:
            key: Ключ факта

        Returns:
            Значение факта если найдено
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT value FROM semantic_memories WHERE key = ?",
                (key,),
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                self._record_access(key)
                return result[0]

            return None

        except Exception as e:
            logger.error(f"❌ Ошибка получения semantic memory: {e}")
            return None

    def add_working_memory(self, content: str) -> None:
        """
        Добавить в рабочую память.

        Args:
            content: Содержимое
        """
        self.working_memory.append({
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        logger.debug("⚡ Элемент добавлен в рабочую память")

    def get_working_memory(self) -> List[Dict[str, str]]:
        """Получить рабочую память."""
        return list(self.working_memory)

    def clear_working_memory(self) -> None:
        """Очистить рабочую память."""
        self.working_memory.clear()
        logger.info("🗑️ Рабочая память очищена")

    def _update_knowledge_graph(
        self,
        entity1: str,
        relation: str,
        entity2: str,
    ) -> None:
        """Обновить граф знаний."""
        if not self.knowledge_graph:
            return

        try:
            self.knowledge_graph.add_edge(entity1, entity2, relation=relation)
            logger.debug(f"📊 Граф знаний обновлен: {entity1} -> {entity2}")
        except Exception as e:
            logger.debug(f"⚠️ Ошибка обновления графа: {e}")

    def _record_access(self, key: str) -> None:
        """Записать доступ к памяти."""
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
        self.last_access[key] = datetime.now()

    def cleanup_old_memories(self, days: int = 30) -> int:
        """
        Удалить старые воспоминания (забывание).

        Args:
            days: Удалить старше чем N дней

        Returns:
            Количество удаленных воспоминаний
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute("""
                DELETE FROM episodic_memories
                WHERE timestamp < ? AND importance < 0.3
            """, (cutoff_date,))

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"🗑️ Удалено {deleted_count} старых воспоминаний")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Ошибка очистки памяти: {e}")
            return 0

    def get_memory_stats(self) -> Dict[str, Any]:
        """Получить статистику памяти."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM episodic_memories")
            episodic_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM semantic_memories")
            semantic_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM procedural_memories")
            procedural_count = cursor.fetchone()[0]

            conn.close()

            return {
                "episodic": episodic_count,
                "semantic": semantic_count,
                "procedural": procedural_count,
                "working": len(self.working_memory),
                "knowledge_graph_nodes": (
                    len(self.knowledge_graph.nodes) if self.knowledge_graph else 0
                ),
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}

    def __repr__(self) -> str:
        """Строковое представление."""
        return "EnhancedMemory()"