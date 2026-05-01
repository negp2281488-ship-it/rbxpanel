#!/bin/bash
# Production запуск с Gunicorn

echo "🚀 Запуск Roblox Cookie Checker API (Production Mode)"
echo "=================================================="

# Проверка зависимостей
if ! command -v gunicorn &> /dev/null; then
    echo "❌ Gunicorn не установлен!"
    echo "Установите: pip install -r requirements.txt"
    exit 1
fi

# Переход в директорию скрипта
cd "$(dirname "$0")"

# Загрузка прокси (если нужно)
if [ -f "proxies.txt" ]; then
    PROXY_COUNT=$(wc -l < proxies.txt)
    echo "✅ Найдено $PROXY_COUNT прокси в proxies.txt"
else
    echo "⚠️  Файл proxies.txt не найден!"
fi

echo ""
echo "Запуск Gunicorn..."
echo "=================================================="

# Запуск Gunicorn
exec gunicorn \
    --config gunicorn_config.py \
    flask_api:app

