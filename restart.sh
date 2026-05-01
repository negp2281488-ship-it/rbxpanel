#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
mkdir -p "$SCRIPT_DIR/logs"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓ $*${NC}"; }
fail() { echo -e "${RED}  ✗ $*${NC}"; exit 1; }
warn() { echo -e "${YELLOW}  ! $*${NC}"; }

echo "=========================================="
echo "  RBXPanel - Restart"
echo "=========================================="
echo ""

# ── 1. Dependencies ───────────────────────────────────────────
echo "[1/4] Installing dependencies..."

setup_venv() {
    local DIR="$1"
    local NAME="$2"
    if [ ! -d "$DIR" ]; then warn "$NAME directory not found, skipping"; return 1; fi
    if [ ! -f "$DIR/requirements.txt" ]; then warn "No requirements.txt in $NAME, skipping"; return 1; fi

    echo "  Setting up venv for $NAME..."
    python3 -m venv "$DIR/venv" 2>/dev/null
    "$DIR/venv/bin/pip" install --upgrade pip -q 2>/dev/null
    "$DIR/venv/bin/pip" install -r "$DIR/requirements.txt" -q 2>&1
    if [ $? -eq 0 ]; then ok "$NAME dependencies installed"
    else warn "$NAME dependencies had errors, continuing..."; fi
}

setup_venv "$SCRIPT_DIR/roblox_api" "API"
setup_venv "$SCRIPT_DIR/site" "Site"
echo ""

# ── 2. Stop ───────────────────────────────────────────────────
echo "[2/4] Stopping services..."

pkill -f "flask_api.py"   2>/dev/null
pkill -f "gunicorn.*app"  2>/dev/null
pkill -f "python3.*app.py" 2>/dev/null

for PORT in 80 8081; do
    PID=$(lsof -ti:$PORT 2>/dev/null)
    [ -n "$PID" ] && kill -9 $PID 2>/dev/null && echo "  Killed PID $PID on port $PORT"
done

sleep 2
ok "Services stopped"
echo ""

# ── 3. Start ──────────────────────────────────────────────────
echo "[3/4] Starting services..."

# API
if [ -f "$SCRIPT_DIR/roblox_api/flask_api.py" ] && [ -f "$SCRIPT_DIR/roblox_api/venv/bin/python" ]; then
    echo "  Starting API (port 8081)..."
    cd "$SCRIPT_DIR/roblox_api"
    nohup "$SCRIPT_DIR/roblox_api/venv/bin/gunicorn" \
        -w 2 -b 127.0.0.1:8081 flask_api:app \
        > "$SCRIPT_DIR/logs/api.log" 2>&1 &
    ok "API started (PID: $!)"
else
    warn "API not found or venv missing, skipping"
fi

# Site
if [ -f "$SCRIPT_DIR/site/app.py" ] && [ -f "$SCRIPT_DIR/site/venv/bin/python" ]; then
    echo "  Starting Site (port 80)..."
    cd "$SCRIPT_DIR/site"
    nohup "$SCRIPT_DIR/site/venv/bin/gunicorn" \
        -w 1 -b 0.0.0.0:80 app:app \
        > "$SCRIPT_DIR/logs/site.log" 2>&1 &
    ok "Site started (PID: $!)"
else
    warn "Site not found or venv missing, skipping"
fi

sleep 3
cd "$SCRIPT_DIR"
echo ""

# ── 4. Check ─────────────────────────────────────────────────
echo "[4/4] Checking..."

check_port() {
    local PORT="$1"; local NAME="$2"
    if ss -tlnp 2>/dev/null | grep -q ":$PORT " || lsof -ti:$PORT >/dev/null 2>&1; then
        ok "$NAME is running (port $PORT)"
    else
        warn "$NAME not detected on port $PORT — check logs/$( [ $PORT -eq 80 ] && echo site || echo api ).log"
    fi
}

check_port 8081 "API"
check_port 80   "Site"

echo ""
echo "=========================================="
echo "  Done!"
echo "=========================================="
echo ""
IP=$(hostname -I | awk '{print $1}')
echo "  Site: http://$IP"
echo "  API:  http://127.0.0.1:8081"
echo ""
echo "  Logs:"
echo "    tail -f $SCRIPT_DIR/logs/site.log"
echo "    tail -f $SCRIPT_DIR/logs/api.log"
echo ""
