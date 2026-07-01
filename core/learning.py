"""
Модуль самообучения и адаптации ассистента.

Отслеживает успешность ответов, предпочтения пользователя,
и адаптирует поведение на основе собранных данных.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
import sqlite3
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseQuality(Enum):
    """Качество ответа."""
    EXCELLENT = 5
    GOOD = 4
    NEUTRAL = 3
    POOR = 2
    BAD = 1


class UserFeedback(Enum):
    """Тип отзыва пользователя."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    CLARIFICATION = "clarification"
    INCOMPLETE = "incomplete"


@dataclass
class ResponseMetric:
    """Метрика ответа."""
    response_id: str
    timestamp: str
    query: str
    response: str
    model_used: str
    execution_time: float
    quality_score: int
    user_feedback: Optional[str] = None
    clarifications_asked: int = 0
    action_completed: bool = True
    tags: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserPreference:
    """Предпочтение пользователя."""
    preference_type: str  # verbosity, format, language, focus, time_preference
    value: str
    confidence: float
    last_updated: str
    usage_count: int = 1


class LearningEngine:
    """Основной модуль обучения."""

    def __init__(self, db_path: str = "learning.db"):
        """
        Инициализация.

        Args:
            db_path: Путь к БД обучения
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.metrics: List[ResponseMetric] = []
        self.preferences: Dict[str, UserPreference] = {}
        self.patterns: List[Dict[str, Any]] = []

        self._init_database()
        self._load_data()

        logger.info("🧠 LearningEngine инициализирован")

    def _init_database(self) -> None:
        """Инициализировать БД."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Таблица метрик ответов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_metrics (
                    response_id TEXT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    query TEXT NOT NULL,
                    response TEXT,
                    model_used TEXT,
                    execution_time REAL,
                    quality_score INTEGER,
                    user_feedback TEXT,
                    clarifications_asked INTEGER DEFAULT 0,
                    action_completed BOOLEAN DEFAULT 1,
                    tags TEXT,
                    context_data TEXT
                )
            """)

            # Таблица предпочтений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    preference_id TEXT PRIMARY KEY,
                    preference_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 1
                )
            """)

            # Таблица паттернов поведения
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS behavior_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    frequency INTEGER,
                    last_observed DATETIME,
                    confidence REAL
                )
            """)

            conn.commit()
            conn.close()

            logger.info("✅ БД обучения инициализирована")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")

    def _load_data(self) -> None:
        """Загрузить данные из БД."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Загружаем метрики
            cursor.execute("SELECT * FROM response_metrics ORDER BY timestamp DESC LIMIT 1000")
            for row in cursor.fetchall():
                # Парсим данные
                pass

            # Загружаем предпочтения
            cursor.execute("SELECT * FROM user_preferences")
            for row in cursor.fetchall():
                pass

            conn.close()

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных: {e}")

    def log_response(
        self,
        response_id: str,
        query: str,
        response: str,
        model_used: str,
        execution_time: float,
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Логировать ответ для анализа.

        Args:
            response_id: ID ответа
            query: Исходный запрос
            response: Ответ ассистента
            model_used: Использованная модель
            execution_time: Время выполнения
            tags: Теги для категоризации
        """
        try:
            metric = ResponseMetric(
                response_id=response_id,
                timestamp=datetime.now().isoformat(),
                query=query,
                response=response,
                model_used=model_used,
                execution_time=execution_time,
                quality_score=3,  # Начальная оценка
                tags=tags or [],
            )

            self.metrics.append(metric)
            self._save_metric(metric)

            logger.debug(f"✅ Ответ залогирован: {response_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка логирования ответа: {e}")

    def _save_metric(self, metric: ResponseMetric) -> None:
        """Сохранить метрику в БД."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO response_metrics
                (response_id, timestamp, query, response, model_used, execution_time,
                 quality_score, user_feedback, clarifications_asked, action_completed, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.response_id,
                metric.timestamp,
                metric.query,
                metric.response,
                metric.model_used,
                metric.execution_time,
                metric.quality_score,
                metric.user_feedback,
                metric.clarifications_asked,
                metric.action_completed,
                json.dumps(metric.tags),
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения метрики: {e}")

    def record_feedback(
        self,
        response_id: str,
        feedback_type: UserFeedback,
        quality_score: Optional[int] = None,
        clarifications: int = 0,
        completed: bool = True,
    ) -> None:
        """
        Записать отзыв пользователя.

        Args:
            response_id: ID ответа
            feedback_type: Тип отзыва
            quality_score: Оценка качества (1-5)
            clarifications: Количество уточнений
            completed: Выполнено ли действие
        """
        try:
            # Находим метрику
            metric = next(
                (m for m in self.metrics if m.response_id == response_id),
                None,
            )

            if metric:
                metric.user_feedback = feedback_type.value
                if quality_score:
                    metric.quality_score = quality_score
                metric.clarifications_asked = clarifications
                metric.action_completed = completed

                self._save_metric(metric)

                # Анализируем обратную связь
                self._analyze_feedback(metric)

                logger.info(f"✅ Отзыв записан: {response_id} ({feedback_type.value})")

        except Exception as e:
            logger.error(f"❌ Ошибка записи отзыва: {e}")

    def _analyze_feedback(self, metric: ResponseMetric) -> None:
        """
        Анализировать отзыв и обновить предпочтения.

        Args:
            metric: Метрика ответа
        """
        try:
            # Анализируем качество
            if metric.quality_score >= 4:
                logger.debug(f"🎯 Хороший ответ по {metric.tags}")
                self._boost_strategy(metric)

            elif metric.quality_score <= 2:
                logger.debug(f"📉 Плохой ответ по {metric.tags}")
                self._degrade_strategy(metric)

            # Анализируем необходимость уточнений
            if metric.clarifications_asked > 0:
                logger.debug(f"❓ Требовались уточнения: {metric.clarifications_asked}")
                self._adjust_verbosity(increase=True)

            # Анализируем завершенность
            if not metric.action_completed:
                logger.debug("⚠️ Действие не завершено")
                self._mark_incomplete_pattern(metric)

        except Exception as e:
            logger.error(f"❌ Ошибка анализа отзыва: {e}")

    def _boost_strategy(self, metric: ResponseMetric) -> None:
        """Усилить успешную стратегию."""
        for tag in metric.tags:
            self._update_preference(
                f"strategy_{tag}",
                "positive",
                confidence_increase=0.1,
            )

    def _degrade_strategy(self, metric: ResponseMetric) -> None:
        """Ослабить неудачную стратегию."""
        for tag in metric.tags:
            self._update_preference(
                f"strategy_{tag}",
                "negative",
                confidence_increase=-0.1,
            )

    def _adjust_verbosity(self, increase: bool = True) -> None:
        """Отрегулировать уровень детализации."""
        pref_type = "verbosity"
        current = self.preferences.get(pref_type)

        if current:
            levels = ["minimal", "brief", "standard", "detailed", "comprehensive"]
            current_idx = levels.index(current.value) if current.value in levels else 2

            if increase and current_idx < len(levels) - 1:
                new_level = levels[current_idx + 1]
            elif not increase and current_idx > 0:
                new_level = levels[current_idx - 1]
            else:
                return

            self._update_preference(pref_type, new_level, confidence_increase=0.05)

    def _mark_incomplete_pattern(self, metric: ResponseMetric) -> None:
        """Отметить неполный паттерн."""
        pattern = {
            "type": "incomplete",
            "query_pattern": metric.query[:50],
            "timestamp": datetime.now().isoformat(),
            "frequency": 1,
        }

        existing = next(
            (p for p in self.patterns if p.get("query_pattern") == pattern["query_pattern"]),
            None,
        )

        if existing:
            existing["frequency"] += 1
        else:
            self.patterns.append(pattern)

    def _update_preference(
        self,
        pref_type: str,
        value: str,
        confidence_increase: float = 0.1,
    ) -> None:
        """
        Обновить предпочтение.

        Args:
            pref_type: Тип предпочтения
            value: Новое значение
            confidence_increase: Изменение уверенности
        """
        if pref_type not in self.preferences:
            self.preferences[pref_type] = UserPreference(
                preference_type=pref_type,
                value=value,
                confidence=0.5,
                last_updated=datetime.now().isoformat(),
            )
        else:
            pref = self.preferences[pref_type]
            pref.confidence = min(1.0, pref.confidence + confidence_increase)
            pref.confidence = max(0.0, pref.confidence)
            pref.value = value
            pref.usage_count += 1
            pref.last_updated = datetime.now().isoformat()

    def get_system_prompt_adjustment(self) -> str:
        """
        Получить адаптированный system prompt.

        Returns:
            Адаптированный промпт
        """
        base_prompt = """Ты - персональный AI ассистент на русском языке.
Ты дружелюбный, полезный и всегда стараешься помочь пользователю."""

        # Добавляем адаптации на основе предпочтений
        adjustments = []

        verbosity_pref = self.preferences.get("verbosity")
        if verbosity_pref:
            if verbosity_pref.value == "minimal":
                adjustments.append("Отвечай максимально кратко, 1-2 предложения.")
            elif verbosity_pref.value == "brief":
                adjustments.append("Отвечай кратко и по сути, 2-3 предложения.")
            elif verbosity_pref.value == "detailed":
                adjustments.append("Давай подробные ответы с примерами.")
            elif verbosity_pref.value == "comprehensive":
                adjustments.append("Давай очень подробные ответы со всеми деталями и примерами.")

        format_pref = self.preferences.get("response_format")
        if format_pref:
            if format_pref.value == "list":
                adjustments.append("Используй списки для структурирования информации.")
            elif format_pref.value == "table":
                adjustments.append("Используй таблицы где это уместно.")
            elif format_pref.value == "narrative":
                adjustments.append("Рассказывай историями и примерами.")

        if adjustments:
            base_prompt += "\n\n" + "\n".join(adjustments)

        return base_prompt

    def get_top_preferences(self, limit: int = 5) -> List[Tuple[str, str, float]]:
        """
        Получить топ предпочтения.

        Args:
            limit: Количество предпочтений

        Returns:
            Список (тип, значение, уверенность)
        """
        sorted_prefs = sorted(
            self.preferences.items(),
            key=lambda x: x[1].confidence,
            reverse=True,
        )

        return [
            (pref_type, pref.value, pref.confidence)
            for pref_type, pref in sorted_prefs[:limit]
        ]

    def get_learning_stats(self) -> Dict[str, Any]:
        """Получить статистику обучения."""
        if not self.metrics:
            return {}

        recent_metrics = self.metrics[-100:]  # Последние 100
        quality_scores = [m.quality_score for m in recent_metrics]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        completed_actions = sum(1 for m in recent_metrics if m.action_completed)
        completion_rate = completed_actions / len(recent_metrics) if recent_metrics else 0

        avg_execution_time = sum(m.execution_time for m in recent_metrics) / len(recent_metrics)

        return {
            "total_responses": len(self.metrics),
            "avg_quality_score": avg_quality,
            "completion_rate": completion_rate,
            "avg_execution_time": avg_execution_time,
            "user_preferences": len(self.preferences),
            "detected_patterns": len(self.patterns),
            "top_preferences": self.get_top_preferences(),
        }

    def export_learning_data(self, output_file: str) -> bool:
        """
        Экспортировать данные обучения.

        Args:
            output_file: Файл для экспорта

        Returns:
            True если успешно
        """
        try:
            data = {
                "metrics_count": len(self.metrics),
                "preferences": {
                    k: asdict(v) for k, v in self.preferences.items()
                },
                "patterns": self.patterns,
                "stats": self.get_learning_stats(),
            }

            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"✅ Данные обучения экспортированы: {output_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта: {e}")
            return False

    def __repr__(self) -> str:
        """Строковое представление."""
        return (
            f"LearningEngine("
            f"metrics={len(self.metrics)}, "
            f"preferences={len(self.preferences)})"
        )