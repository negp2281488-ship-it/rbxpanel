#!/bin/bash
# RBXPanel — Installer

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓  $*${NC}"; }
fail() { echo -e "${RED}✗  $*${NC}"; exit 1; }
info() { echo -e "${CYAN}→  $*${NC}"; }
warn() { echo -e "${YELLOW}!  $*${NC}"; }

# ── Root check ────────────────────────────────────────────────
[ "$EUID" -eq 0 ] || fail "Run as root: sudo bash setup.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BASE="/opt/rbxpanel"

echo ""
echo "══════════════════════════════════════════════════"
echo "   RBXPanel — Installer"
echo "══════════════════════════════════════════════════"
echo ""

# ── 1. System packages ────────────────────────────────────────
info "Installing system packages..."
apt-get update -qq 2>/dev/null
apt-get install -y -qq python3 python3-pip python3-venv curl 2>/dev/null
ok "System packages installed"

# ── 2. Copy files ─────────────────────────────────────────────
info "Setting up directories..."
mkdir -p "$INSTALL_BASE"

for DIR in site roblox_api; do
    SRC="$SCRIPT_DIR/$DIR"
    DST="$INSTALL_BASE/$DIR"
    if [ -d "$SRC" ]; then
        info "Copying $DIR → $DST"
        rm -rf "$DST"
        cp -r "$SRC" "$DST"
        ok "$DIR copied"
    else
        warn "$DIR not found in $SCRIPT_DIR, skipping"
    fi
done

# ── 3. Virtual environments ───────────────────────────────────
make_venv() {
    local DIR="$1"
    [ -f "$DIR/requirements.txt" ] || { warn "No requirements.txt in $DIR, skipping venv"; return; }
    info "Creating venv in $DIR..."
    python3 -m venv "$DIR/venv"
    "$DIR/venv/bin/pip" install --upgrade pip -q
    "$DIR/venv/bin/pip" install -r "$DIR/requirements.txt" -q
    ok "venv ready: $DIR"
}

[ -d "$INSTALL_BASE/site" ]       && make_venv "$INSTALL_BASE/site"
[ -d "$INSTALL_BASE/roblox_api" ] && make_venv "$INSTALL_BASE/roblox_api"

# ── 4. Init admin ────────────────────────────────────────────
if [ -f "$INSTALL_BASE/site/init_admin.py" ]; then
    info "Initializing admin..."
    cd "$INSTALL_BASE/site" && "$INSTALL_BASE/site/venv/bin/python" init_admin.py 2>/dev/null && ok "Admin initialized" || warn "init_admin failed"
fi

# ── 5. Systemd services ───────────────────────────────────────
install_service() {
    local NAME="$1"
    local WORKDIR="$2"
    local EXEC="$3"

    cat > "/etc/systemd/system/${NAME}.service" <<EOF
[Unit]
Description=${NAME}
After=network.target

[Service]
WorkingDirectory=${WORKDIR}
ExecStart=${EXEC}
Restart=always
RestartSec=5
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$NAME" 2>/dev/null
    systemctl restart "$NAME"
    sleep 2
    if systemctl is-active --quiet "$NAME"; then
        ok "Service $NAME is running"
    else
        warn "Service $NAME failed — check: journalctl -u $NAME -n 20"
    fi
}

if [ -d "$INSTALL_BASE/site" ]; then
    install_service "rbxsite" \
        "$INSTALL_BASE/site" \
        "$INSTALL_BASE/site/venv/bin/gunicorn -w 2 -b 0.0.0.0:80 app:app"
fi

if [ -d "$INSTALL_BASE/roblox_api" ]; then
    install_service "roblox-api" \
        "$INSTALL_BASE/roblox_api" \
        "$INSTALL_BASE/roblox_api/venv/bin/gunicorn -w 2 -b 127.0.0.1:8081 flask_api:app"
fi

# ── Done ──────────────────────────────────────────────────────
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "══════════════════════════════════════════════════"
echo ""
echo "  Site:       http://${IP}"
echo "  Roblox API: http://127.0.0.1:8081"
echo ""
echo "  Status:  systemctl status rbxsite roblox-api"
echo "  Logs:    journalctl -u rbxsite -f"
echo ""
echo "══════════════════════════════════════════════════"
echo ""
