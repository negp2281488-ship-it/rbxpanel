#!/bin/bash
# ──────────────────────────────────────────────────────────────
#  RBXPanel — запуск всех сервисов (nohup-режим, без systemd)
#  Используй setup.sh для установки через systemd (production)
# ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
mkdir -p "$SCRIPT_DIR/logs"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; exit 1; }
warn() { echo -e "${YELLOW}⚠  $*${NC}"; }

echo ""
echo "══════════════════════════════════════════"
echo "    RBXPanel — запуск"
echo "══════════════════════════════════════════"
echo ""

# ── Проверки ──────────────────────────────────────────────────
command -v python3 &>/dev/null || fail "Python3 не найден!"

# ── Вспомогательная функция: запуск в venv или глобально ─────
run_in_venv() {
    local DIR="$1"; local CMD="$2"; local NAME="$3"; local LOG="$4"
    cd "$DIR"
    if [ -f "venv/bin/python" ]; then
        nohup venv/bin/$CMD > "$LOG" 2>&1 &
    else
        warn "$NAME: venv не найден, запускаю через системный python3"
        nohup python3 $CMD > "$LOG" 2>&1 &
    fi
    echo $!
}

# ── 1. Roblox API (порт 8081) ─────────────────────────────────
echo "▶ Запуск Roblox API (8081)..."
[ -f "$SCRIPT_DIR/roblox_api/flask_api.py" ] || fail "roblox_api/flask_api.py не найден!"
API_PID=$(run_in_venv "$SCRIPT_DIR/roblox_api" "gunicorn -c gunicorn_config.py 'flask_api:app'" "API" "$SCRIPT_DIR/logs/api.log")
sleep 2
if kill -0 "$API_PID" 2>/dev/null; then ok "API запущен (PID $API_PID)"; else fail "API не запустился — смотри logs/api.log"; fi

# ── 2. Site (порт 80) ─────────────────────────────────────────
echo "▶ Запуск Site (80)..."
[ -f "$SCRIPT_DIR/site/app.py" ] || fail "site/app.py не найден!"
SITE_PID=$(run_in_venv "$SCRIPT_DIR/site" "gunicorn --bind 0.0.0.0:80 --workers 2 --worker-class gevent 'app:app'" "Site" "$SCRIPT_DIR/logs/site.log")
sleep 2
if kill -0 "$SITE_PID" 2>/dev/null; then ok "Site запущен (PID $SITE_PID)"; else fail "Site не запустился — смотри logs/site.log"; fi

# ── Итог ──────────────────────────────────────────────────────
cd "$SCRIPT_DIR"
echo ""
echo "══════════════════════════════════════════"
echo ""
echo "  Roblox API   → http://localhost:8081"
echo "  Site         → http://localhost:80"
echo ""
echo "  Логи:  tail -f logs/api.log"
echo "         tail -f logs/site.log"
echo ""
echo "  Остановить: kill \$PID  или  ./stop.sh"
echo ""
