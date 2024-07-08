# Образ на основе которого создаём контейнер
FROM python:3.12-slim

# Рабочая директория внутри проекта
WORKDIR /var/www/geosight

# Переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости для PostgreSQL и другие необходимые пакеты
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-postgis \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Копируем содержимое текущей папки в контейнер
COPY . .
