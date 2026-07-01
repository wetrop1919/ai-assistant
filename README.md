# 🤖 AI Assistant - Персональный AI Ассистент

Модульный персональный AI-ассистент с поддержкой голоса, памяти и навыков. Работает с локальной Ollama (Llama 3) без подключения к интернету. С полным доступом к системе, многоуровневой системой безопасности и поддержкой множества интеграций.

## ✨ Возможности

- 🧠 **Мощный ИИ** - Использует Llama 3 через локальную Ollama
- 🎤 **Распознавание речи** - faster-whisper для русского языка
- 🔊 **Синтез речи** - pyttsx3 + piper-tts для озвучивания ответов
- 💾 **Долговременная память** - SQLite база данных с поиском
- 🎯 **Навыки** - Модульная система расширяемых навыков
- 🔒 **Безопасность** - Режим песочницы для ограничения системных команд
- ⚡ **Асинхронность** - asyncio для неблокирующей работы
- 📝 **Логирование** - Подробные логи с цветным выводом

## ✨ Особенности

- **🧠 Умный мозг** - Llama 3, CodeLlama, Phi-3 через Ollama
- **📚 RAG система** - ChromaDB для работы с собственными документами
- **💾 Расширенная память** - Episodic, Semantic, Procedural
- **🎨 Продвинутый CLI** - Rich UI с автодополнением и горячими клавишами
- **🔐 Безопасность** - Песочница для кода, мониторинг файлов, аудит
- **🔌 Интеграции** - Calendar, Email, Todo, Smart Home, Media и другие
- **⚡ Высокопроизводительность** - Асинхронная архитектура, кеширование
- **🐳 Docker Support** - Легкий деплой с docker-compose


## 🛠️ Требования

- **Python 3.11+**
- **Ollama** (https://ollama.ai)
- **PyAudio** (для распознавания речи)

## 🚀 Быстрый старт

## 📦 Установка

### 1. Установить Ollama

```bash
# Linux
curl https://ollama.ai/install.sh | sh

# macOS
brew install ollama

# Windows
# Скачать installer: https://ollama.ai/download
```

### 2. Запустить Ollama сервер

```bash
ollama serve
```

### 3. Загрузить модели

```bash
# Основная модель (в отдельном терминале)
ollama pull llama3:8b

# Модель для кода (опционально)
ollama pull codellama:13b

# Быстрая модель (опционально)
ollama pull phi3:mini
```

### 4. Клонировать репозиторий

```bash
git clone <repository>
cd ai_assistant
```

### 5. Создать виртуальное окружение

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 6. Установить зависимости

```bash
pip install -r requirements.txt
```

### 7. Настроить конфигурацию

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать .env под свои нужды (опционально)
```

## 🚀 Использование

### Запуск в текстовом режиме

```bash
python main.py --cli
```

### Запуск в голосовом режиме

```bash
python main.py --voice
```

### Запуск в безопасном режиме (рекомендуется)

```bash
python main.py --sandbox
```

### Запуск со всеми опциями

```bash
python main.py --cli --sandbox --debug
```

## 💬 Примеры использования

### Текстовый интерфейс

```
👤 Вы: Привет!
🧠 Думаю...
🤖 Привет! 👋 Как дела? Чем я могу тебе помочь?

👤 Вы: Напиши Python функцию для сортировки
🧠 Думаю...
🤖 Вот функция сортировки:

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

👤 Вы: помощь
📚 Доступные команды:
...
```

### Встроенные команды

| Команда | Описание |
|---------|----------|
| `/stats` | Показать статистику памяти |
| `/clear` | Очистить краткосрочную память |
| `/memory <запрос>` | Поиск в памяти |
| `/export` | Экспортировать воспоминания в JSON |
| `/skills` | Показать список навыков |
| `помощь` | Показать справку |
| `выход` | Выход из приложения |

## 🏗️ Архитектура

```
ai-assistant/
├── ai_assistant/                 # Основной пакет
│   ├── __init__.py
│   ├── main.py                   # Точка входа
│   ├── config.py                 # Конфигурация
│   ├── core/
│   │   ├── brain.py              # Основной мозг
│   │   ├── memory.py             # Система памяти
│   │   ├── security.py           # Безопасность
│   │   ├── rag.py                # RAG система
│   │   ├── router.py             # Маршрутизация
│   │   ├── multimodal.py         # Мультимодальность
│   │   ├── ears.py               # Распознавание речи
│   │   └── voice.py              # Синтез речи
│   ├── skills/
│   │   ├── base.py               # Базовый навык
│   │   ├── system.py             # Управление системой
│   │   ├── files.py              # Файлы
│   │   ├── web.py                # Веб-инструменты
│   │   ├── automation.py         # Автоматизация
│   │   ├── coding.py             # Программирование
│   │   └── registry.py           # Реестр навыков
│   ├── integrations/             # Интеграции
│   │   ├── calendar.py
│   │   ├── email.py
│   │   ├── todo.py
│   │   └── ...
│   ├── ui/
│   │   ├── cli.py                # Главный CLI
│   │   ├── themes.py             # Темы
│   │   ├── formatters.py         # Форматеры
│   │   ├── animations.py         # Анимации
│   │   ├── shortcuts.py          # Горячие клавиши
│   │   └── input_handler.py      # Обработка ввода
│   ├── security/
│   │   ├── policies.py           # Политики
│   │   ├── confirmation.py       # Подтверждения
│   │   └── recovery.py           # Восстановление
│   ├── api/
│   │   └── server.py             # REST API
│   └── utils/
│       ├── logger.py
│       ├── formatters.py
│       └── ...
├── tests/
│   ├── test_security.py
│   ├── test_skills.py
│   ├── test_integrations.py
│   └── ...
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── skills.md
│   └── ...
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── config.yaml
├── pyproject.toml
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── .github/
    └── workflows/
        └── ci.yml
```

## ⚙️ Конфигурация

Все параметры конфигурируются через файл `.env`:

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:8b
OLLAMA_TIMEOUT=30

# Речь
WAKE_WORDS=ассистент,слушай,компьютер
WHISPER_MODEL=medium
TTS_ENGINE=pyttsx3

# Режимы
SANDBOX_MODE=true
VOICE_MODE=true

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=detailed
```

## 🔒 Безопасность

### Режим песочницы (SANDBOX_MODE)

Когда включен `SANDBOX_MODE=true`:
- ❌ Запрещены системные команды (exec, eval)
- ❌ Нет доступа к файловой системе
- ❌ Нет запуска внешних процессов
- ✅ Только распознавание и обработка текста

### Логирование

Все действия логируются в `assistant.log`:

```
[2024-01-15 10:30:45] INFO     core.brain:check_connection:42 ✅ Ollama доступна
[2024-01-15 10:30:46] INFO     core.memory:add_short_term:89 📝 Добавлено в краткосрочную память: user
```

## 🤝 Добавление собственных навыков

Создайте новый файл `skills/my_skill.py`:

```python
from skills.base import Skill

class MySkill(Skill):
    def __init__(self):
        super().__init__(
            name="my_skill",
            description="Описание навыка"
        )
    
    def can_handle(self, prompt: str) -> bool:
        return "ключевое_слово" in prompt.lower()
    
    async def execute(self, prompt: str) -> str:
        return "Результат выполнения навыка"
```

Затем зарегистрируйте в `ui/cli.py`:

```python
from skills.my_skill import MySkill

self.skills.register(MySkill())
```

## 🐛 Отладка

Включить режим отладки:

```bash
python main.py --debug
```

Это выведет дополнительные логи и замедлит обработку для удобства отладки.

## 📊 Статистика памяти

Команда `/stats` выводит:

```
📊 Статистика памяти:
  • Всего воспоминаний: 42
  • Сообщений пользователя: 20
  • Ответов ассистента: 22
  • Краткосрочная память: 20/20
```

## 🚦 Решение проблем

### Ollama не запускается

```bash
# Проверить установку
ollama --version

# Запустить сервер вручную
ollama serve
```

### Модель не загружается

```bash
# Проверить загруженные модели
ollama list

# Загрузить модель
ollama pull llama3:8b
```

### Ошибка PyAudio на Linux

```bash
# Установить зависимости
sudo apt-get install python3-dev portaudio19-dev

# Переустановить пакет
pip install --force-reinstall pyaudio
```

### Голос не работает

```bash
# Проверить доступные голоса
python -c "import pyttsx3; e=pyttsx3.init(); print([v.name for v in e.getProperty('voices')])"
```

## 📝 Лицензия

MIT License - Свободно используйте в своих проектах!

## 🙏 Благодарности

- [Ollama](https://ollama.ai) - Локальные LLM
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Распознавание речи
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Синтез речи
- [Llama](https://llama.meta.com) - Мощная языковая модель

## 📧 Контакты

Если у вас есть вопросы или предложения, создавайте Issues в репозитории!

---

**Версия**: 0.2.1 
**Последнее обновление**: 2026 
**Статус**: 🚀 В разработке

---