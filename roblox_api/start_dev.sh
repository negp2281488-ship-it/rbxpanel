#!/bin/bash
# Development запуск (для тестирования)

echo "🔧 Запуск Roblox Cookie Checker API (Development Mode)"
echo "=================================================="

# Переход в директорию скрипта
cd "$(dirname "$0")"

# Загрузка прокси
if [ -f "proxies.txt" ]; then
    PROXY_COUNT=$(wc -l < proxies.txt)
    echo "✅ Найдено $PROXY_COUNT прокси в proxies.txt"
else
    echo "⚠️  Файл proxies.txt не найден!"
fi

echo ""
echo "Запуск Flask Dev Server..."
echo "⚠️  Для production используйте: ./start_production.sh"
echo "=================================================="

# Запуск Flask dev server
python flask_api.py

