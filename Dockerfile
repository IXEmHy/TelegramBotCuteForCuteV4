# ============================================
# Используем Python 3.13 (latest stable)
# ============================================
FROM python:3.13-slim

# Метаданные образа
LABEL maintainer="your_email@example.com"
LABEL description="TelegramBotCuteForCuteV4 - Python 3.13"
LABEL version="1.0.0"

# Отключаем буферизацию Python для логов в реальном времени
ENV PYTHONUNBUFFERED=1
# Не создавать .pyc файлы (экономия места)
ENV PYTHONDONTWRITEBYTECODE=1
# Используем UTF-8 по умолчанию
ENV PYTHONIOENCODING=UTF-8

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей
# gcc, g++ - для компиляции Python расширений (asyncpg)
# postgresql-client - CLI для PostgreSQL
# libpq-dev - библиотеки для asyncpg
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean 

# Обновляем pip, setuptools, wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Копируем только requirements.txt (для кеширования слоя)
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Создаем директорию для логов с правильными правами
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Проверка установки (опционально, для отладки)
RUN python --version && pip list

# Healthcheck для Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Запуск приложения
CMD ["python", "-m", "bot.main"]
