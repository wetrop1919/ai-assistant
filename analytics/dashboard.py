"""
Аналитический дашборд для отслеживания прогресса обучения.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.text import Text

logger = logging.getLogger(__name__)

console = Console()


class Dashboard:
    """Аналитический дашборд."""

    def __init__(self, learning_engine=None):
        """
        Инициализация.

        Args:
            learning_engine: Модуль обучения
        """
        self.learning_engine = learning_engine

    def show_main_dashboard(self) -> None:
        """Показать главный дашборд."""
        if not self.learning_engine:
            console.print("[red]Learning engine not available[/red]")
            return

        stats = self.learning_engine.get_learning_stats()

        # Заголовок
        console.print("\n[bold cyan]📊 Learning Dashboard[/bold cyan]\n")

        # Основные метрики
        metrics_table = Table(title="Main Metrics", show_header=True)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")

        metrics_table.add_row(
            "Total Responses",
            f"{stats.get('total_responses', 0):,}",
        )

        metrics_table.add_row(
            "Average Quality",
            f"{stats.get('avg_quality_score', 0):.2f}/5.0",
        )

        metrics_table.add_row(
            "Completion Rate",
            f"{stats.get('completion_rate', 0):.1%}",
        )

        metrics_table.add_row(
            "Avg Response Time",
            f"{stats.get('avg_execution_time', 0):.2f}s",
        )

        metrics_table.add_row(
            "User Preferences",
            str(stats.get('user_preferences', 0)),
        )

        console.print(metrics_table)

        # Предпочтения
        self._show_preferences()

        # Паттерны
        self._show_patterns()

    def _show_preferences(self) -> None:
        """Показать предпочтения."""
        if not self.learning_engine:
            return

        prefs_table = Table(title="Learned Preferences", show_header=True)
        prefs_table.add_column("Preference", style="cyan")
        prefs_table.add_column("Value", style="yellow")
        prefs_table.add_column("Confidence", style="green")

        for pref_type, value, confidence in self.learning_engine.get_top_preferences():
            confidence_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
            prefs_table.add_row(
                pref_type,
                value,
                f"[{confidence_bar}] {confidence:.0%}",
            )

        console.print(prefs_table)

    def _show_patterns(self) -> None:
        """Показать обнаруженные паттерны."""
        if not self.learning_engine or not self.learning_engine.patterns:
            return

        patterns_table = Table(title="Behavior Patterns", show_header=True)
        patterns_table.add_column("Pattern", style="cyan")
        patterns_table.add_column("Frequency", style="yellow")

        for pattern in self.learning_engine.patterns[:5]:
            patterns_table.add_row(
                pattern.get("query_pattern", "Unknown")[:40],
                str(pattern.get("frequency", 0)),
            )

        console.print(patterns_table)

    def show_quality_trends(self) -> None:
        """Показать тренды качества."""
        if not self.learning_engine or not self.learning_engine.metrics:
            return

        console.print("\n[bold cyan]📈 Quality Trends[/bold cyan]\n")

        # Берем последние 10 метрик
        recent = self.learning_engine.metrics[-10:]

        trend_table = Table(show_header=True)
        trend_table.add_column("Time", style="cyan")
        trend_table.add_column("Quality", style="yellow")
        trend_table.add_column("Feedback", style="green")

        for metric in recent:
            feedback = metric.user_feedback or "No feedback"
            quality_bar = "█" * metric.quality_score + "░" * (5 - metric.quality_score)

            trend_table.add_row(
                metric.timestamp[-8:],  # Показываем время
                f"[{quality_bar}] {metric.quality_score}/5",
                feedback,
            )

        console.print(trend_table)

    def export_dashboard(self, output_file: str) -> bool:
        """
        Экспортировать дашборд.

        Args:
            output_file: Файл для экспорта

        Returns:
            True если успешно
        """
        try:
            if not self.learning_engine:
                return False

            data = {
                "timestamp": datetime.now().isoformat(),
                "stats": self.learning_engine.get_learning_stats(),
                "preferences": {
                    k: v.value
                    for k, v in self.learning_engine.preferences.items()
                },
            }

            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"✅ Дашборд экспортирован: {output_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка экспорта дашборда: {e}")
            return False

    def __repr__(self) -> str:
        """Строковое представление."""
        return "Dashboard()"