"""
Навык веб-инструментов.

Возможности:
- Поиск в интернете
- Получение страниц
- Загрузка файлов
- Проверка интернета
- Погода
- Перевод
- Новости
- Сокращение ссылок
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from .base import BaseSkill

logger = logging.getLogger(__name__)


class WebTools(BaseSkill):
    """Веб-инструменты."""

    def __init__(self, brain=None, memory=None):
        """Инициализация навыка веб-инструментов."""
        super().__init__(
            name="web_tools",
            description="Работа с веб: поиск, загрузка, погода, новости",
            version="1.0.0",
            priority=50,
            brain=brain,
            memory=memory,
        )

    def can_handle(self, prompt: str) -> bool:
        """Проверить, может ли обработать запрос."""
        keywords = [
            "поиск в интернете", "найди в веб", "погода", "новости",
            "перевод", "скачай", "загрузи", "интернет",
        ]
        return any(kw in prompt.lower() for kw in keywords)

    def get_capabilities(self) -> List[str]:
        """Получить список возможностей."""
        return [
            "search_web - поиск в интернете",
            "fetch_page - получение содержимого страницы",
            "download_file - загрузка файла",
            "check_connectivity - проверка интернета",
            "get_weather - получить погоду",
            "translate_text - перевод текста",
            "get_news - получить новости",
            "url_shorten - сокращение ссылки",
        ]

    async def execute(self, prompt: str) -> str:
        """Выполнить команду веб-инструмента."""
        try:
            prompt_lower = prompt.lower()

            if "поиск" in prompt_lower or "найди в веб" in prompt_lower:
                return await self._search_web(prompt)

            elif "погода" in prompt_lower:
                return await self._get_weather(prompt)

            elif "новости" in prompt_lower:
                return await self._get_news(prompt)

            elif "перевод" in prompt_lower:
                return await self._translate(prompt)

            elif "интернет" in prompt_lower:
                return await self._check_connectivity()

            elif "загрузи" in prompt_lower or "скачай" in prompt_lower:
                return await self._download_file(prompt)

            else:
                return "🤖 Веб-команда не распознана"

        except Exception as e:
            self.log_action(
                "execute",
                status="error",
                details={"error": str(e)},
                level="ERROR",
            )
            return f"❌ Ошибка: {e}"

    async def _search_web(self, prompt: str) -> str:
        """Поиск в интернете."""
        try:
            import requests

            query = prompt.replace("поиск", "").replace("найди в веб", "").strip()

            if not query:
                return "❌ Укажите поисковый запрос"

            # DuckDuckGo поиск (бесплатный API)
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            response = requests.get(url, timeout=5)
            data = response.json()

            result = f"🔍 Результаты поиска по запросу '{query}':\n\n"

            if data.get("RelatedTopics"):
                for i, topic in enumerate(data["RelatedTopics"][:5], 1):
                    if "Text" in topic:
                        result += f"{i}. {topic['Text'][:100]}...\n"

            self.log_action(
                "search_web",
                status="success",
                details={"query": query},
            )

            return result if result else "❌ Результатов не найдено"

        except ImportError:
            return "⚠️ Требуется requests: pip install requests"
        except Exception as e:
            return f"❌ Ошибка поиска: {e}"

    async def _get_weather(self, prompt: str) -> str:
        """Получить погоду."""
        try:
            import requests

            city = prompt.replace("погода", "").strip()
            if not city:
                city = "Moscow"

            # Open-Meteo (бесплатный API, без ключа)
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            response = requests.get(url, timeout=5)
            data = response.json()

            if not data.get("results"):
                return f"❌ Город '{city}' не найден"

            location = data["results"][0]
            lat, lon = location["latitude"], location["longitude"]

            # Получаем погоду
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m"
            weather_data = requests.get(weather_url, timeout=5).json()
            current = weather_data["current"]

            result = f"""
🌤️ Погода в {location['name']}, {location.get('country', '')}:

🌡️ Температура: {current['temperature_2m']}°C
💨 Ветер: {current['wind_speed_10m']} км/ч
🌐 Координаты: {lat}, {lon}
"""
            self.log_action(
                "get_weather",
                status="success",
                details={"city": city, "temp": current['temperature_2m']},
            )

            return result

        except ImportError:
            return "⚠️ Требуется requests: pip install requests"
        except Exception as e:
            return f"❌ Ошибка получения погоды: {e}"

    async def _translate(self, prompt: str) -> str:
        """Перевод текста."""
        try:
            from translate import Translator

            text = prompt.replace("перевод", "").strip()

            if not text:
                return "❌ Укажите текст для перевода"

            translator = Translator(from_lang="ru", to_lang="en")
            translated = translator.translate(text)

            self.log_action(
                "translate_text",
                status="success",
                details={"length": len(text)},
            )

            return f"🌐 Перевод:\n'{text}' → '{translated}'"

        except ImportError:
            return "⚠️ Требуется translate: pip install translate"
        except Exception as e:
            return f"❌ Ошибка перевода: {e}"

    async def _get_news(self, prompt: str) -> str:
        """Получить новости."""
        topic = prompt.replace("новости", "").strip() or "top"

        result = f"""
📰 Новости ({topic}):

[Новости требуют API RSS-фидов]
Примеры источников:
  • BBC News
  • Reuters
  • CNN
"""
        self.log_action(
            "get_news",
            status="info",
            details={"topic": topic},
        )

        return result

    async def _check_connectivity(self) -> str:
        """Проверить интернет-соединение."""
        try:
            import requests

            response = requests.get("https://www.google.com", timeout=2)

            if response.status_code == 200:
                self.log_action(
                    "check_connectivity",
                    status="success",
                    details={"connected": True},
                )
                return "✅ Интернет-соединение активно"

        except:
            self.log_action(
                "check_connectivity",
                status="warning",
                details={"connected": False},
            )
            return "❌ Нет интернет-соединения"

    async def _download_file(self, prompt: str) -> str:
        """Загрузить файл."""
        if self.sandbox_mode:
            self.log_action(
                "download_file",
                status="simulated",
            )
            return "🔒 [SIMULATED] Файл загружен: document.pdf (2.5 MB)"

        return "ℹ️ Загрузка требует указания URL"

    def __repr__(self) -> str:
        """Строковое представление."""
        return "WebTools()"
