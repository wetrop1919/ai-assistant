FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем рабочее пространство
RUN mkdir -p workspace logs

# Выставляем порт
EXPOSE 8001

# Запускаем приложение
CMD ["python", "main.py", "--mode", "server", "--port", "8001"]