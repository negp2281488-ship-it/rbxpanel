#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  RBXPanel - Stop Script"
echo "=========================================="
echo ""

echo "Остановка сервисов..."
echo ""

# Остановка через pkill
pkill -f "flask_api.py" 2>/dev/null
pkill -f "site/app.py" 2>/dev/null
pkill -f "python3.*flask_api.py" 2>/dev/null
pkill -f "python3.*site/app.py" 2>/dev/null

# Остановка через порты (если lsof установлен)
if command -v lsof &> /dev/null; then
    API_PID=$(lsof -ti:8081 2>/dev/null)
    if [ ! -z "$API_PID" ]; then
        echo "  Остановка API (PID: $API_PID)..."
        kill -9 $API_PID 2>/dev/null
        echo "  ✅ API остановлен"
    else
        echo "  ⚠️  API не запущен"
    fi
    
    SITE_PID=$(sudo lsof -ti:80 2>/dev/null)
    if [ ! -z "$SITE_PID" ]; then
        echo "  Остановка Site (PID: $SITE_PID)..."
        sudo kill -9 $SITE_PID 2>/dev/null
        echo "  ✅ Site остановлен"
    else
        echo "  ⚠️  Site не запущен"
    fi
else
    echo "  ⚠️  lsof не установлен, использован pkill"
    echo "  ✅ Процессы остановлены"
fi

sleep 1

echo ""
echo "=========================================="
echo "  Сервисы остановлены"
echo "=========================================="
echo ""
