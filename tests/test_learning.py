"""
Тесты модуля обучения.
"""

import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from core.learning import LearningEngine, UserFeedback, ResponseMetric
from core.proactive import ProactiveAgent, ProactiveActionType
from analytics.dashboard import Dashboard


class TestLearningEngine:
    """Тесты LearningEngine."""

    def test_initialization(self):
        """Тест инициализации."""
        engine = LearningEngine()
        assert engine is not None
        assert len(engine.metrics) == 0
        assert len(engine.preferences) == 0

    def test_log_response(self):
        """Тест логирования ответа."""
        engine = LearningEngine()
        engine.log_response(
            response_id="test_1",
            query="Test query",
            response="Test response",
            model_used="llama3:8b",
            execution_time=0.5,
            tags=["test"],
        )

        assert len(engine.metrics) == 1
        assert engine.metrics[0].response_id == "test_1"

    def test_record_feedback(self):
        """Тест записи отзыва."""
        engine = LearningEngine()
        engine.log_response(
            response_id="test_1",
            query="Test",
            response="Test",
            model_used="test",
            execution_time=0.5,
        )

        engine.record_feedback(
            response_id="test_1",
            feedback_type=UserFeedback.POSITIVE,
            quality_score=5,
        )

        metric = engine.metrics[0]
        assert metric.user_feedback == UserFeedback.POSITIVE.value
        assert metric.quality_score == 5

    def test_get_system_prompt_adjustment(self):
        """Тест адаптации system prompt."""
        engine = LearningEngine()
        engine._update_preference("verbosity", "brief")

        prompt = engine.get_system_prompt_adjustment()
        assert "кратко" in prompt.lower()

    def test_get_learning_stats(self):
        """Тест получения статистики."""
        engine = LearningEngine()
        engine.log_response(
            response_id="test_1",
            query="Test",
            response="Test",
            model_used="test",
            execution_time=0.5,
        )

        stats = engine.get_learning_stats()
        assert stats["total_responses"] == 1
        assert "avg_quality_score" in stats


class TestProactiveAgent:
    """Тесты ProactiveAgent."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Тест инициализации."""
        agent = ProactiveAgent()
        assert agent is not None
        assert len(agent.pending_actions) == 0

    @pytest.mark.asyncio
    async def test_analyze_and_predict(self):
        """Тест анализа и предсказания."""
        agent = ProactiveAgent()
        actions = await agent.analyze_and_predict()

        assert isinstance(actions, list)

    @pytest.mark.asyncio
    async def test_execute_action(self):
        """Тест выполнения действия."""
        from core.proactive import ProactiveAction

        agent = ProactiveAgent()
        action = ProactiveAction(
            action_type=ProactiveActionType.MORNING_BRIEFING,
            priority=4,
            message="Test",
        )

        result = await agent.execute_action(action)
        assert result == True


class TestDashboard:
    """Тесты Dashboard."""

    def test_initialization(self):
        """Тест инициализации."""
        dashboard = Dashboard()
        assert dashboard is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])