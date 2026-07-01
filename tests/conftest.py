"""
Конфигурация pytest и общие fixtures.
"""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Добавляем корневую директорию
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Мокируем зависимости если их нет
sys.modules['chromadb'] = MagicMock()
sys.modules['chromadb.config'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['networkx'] = MagicMock()
sys.modules['psutil'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()
sys.modules['webrtcvad'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()


@pytest.fixture
def mock_config():
    """Мок конфигурации."""
    config = MagicMock()
    config.mode.cli_mode = True
    config.mode.voice_mode = False
    config.mode.sandbox_mode = True
    config.debug = False
    config.version = "0.2.0"
    config.ollama.host = "http://localhost:11434"
    config.ollama.model = "llama3:8b"
    config.ollama.code_model = "codellama:13b"
    config.ollama.fast_model = "phi3:mini"
    config.ollama.timeout = 30
    config.ollama.temperature_general = 0.7
    config.ollama.temperature_code = 0.2
    config.speech.wake_words = ["ассистент"]
    config.speech.whisper_model = "medium"
    config.speech.tts_engine = "pyttsx3"
    config.memory.db_path = ":memory:"
    config.memory.short_term_size = 20
    return config


@pytest.fixture
def mock_brain():
    """Мок мозга."""
    brain = AsyncMock()
    brain.is_available = True
    brain.generate = AsyncMock(return_value="Test response")
    brain.rag_system = None
    brain.memory = None
    brain.multimodal = None
    brain.health = MagicMock()
    brain.get_status = MagicMock(return_value={"available": True})
    return brain


@pytest.fixture
def mock_memory():
    """Мок памяти."""
    memory = MagicMock()
    memory.add_episodic_memory = MagicMock(return_value=1)
    memory.add_semantic_memory = MagicMock(return_value=True)
    memory.get_semantic_memory = MagicMock(return_value="test_value")
    memory.add_working_memory = MagicMock()
    memory.get_working_memory = MagicMock(return_value=[])
    memory.get_memory_stats = MagicMock(return_value={
        "episodic": 0,
        "semantic": 0,
        "procedural": 0,
        "working": 0,
    })
    return memory


@pytest.fixture
def mock_ollama(monkeypatch):
    """Мок Ollama сервера."""
    import requests

    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = {"models": [{"name": "llama3:8b"}]}

    mock_post = MagicMock()
    mock_post.status_code = 200
    mock_post.json.return_value = {
        "message": {"content": "Test response"}
    }

    monkeypatch.setattr(requests, "get", MagicMock(return_value=mock_get))
    monkeypatch.setattr(requests, "post", MagicMock(return_value=mock_post))

    return mock_get, mock_post


@pytest.fixture
def temp_db(tmp_path):
    """Временная БД для тестов."""
    db_path = tmp_path / "test_memory.db"
    return str(db_path)