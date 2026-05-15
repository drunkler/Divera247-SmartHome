#!/bin/bash
set -e

# ─── Farben ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
info() { echo -e "${CYAN}→${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
fail() { echo -e "${RED}✗ FEHLER:${NC} $1"; exit 1; }
header() { echo -e "\n${BOLD}$1${NC}"; }

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="divera-shelly"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV="$APP_DIR/.venv"
RUN_USER="${SUDO_USER:-$(whoami)}"

echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   Divera247 → Shelly  –  Linux Installer ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Root-Check ────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    fail "Bitte als root ausführen:  sudo bash install.sh"
fi

# ─── Paketmanager erkennen ─────────────────────────────────────────────────────
header "1/5  Systemabhängigkeiten prüfen"

if   command -v apt-get &>/dev/null; then PKG="apt"
elif command -v dnf     &>/dev/null; then PKG="dnf"
elif command -v pacman  &>/dev/null; then PKG="pacman"
else fail "Kein unterstützter Paketmanager gefunden (apt/dnf/pacman)."
fi
info "Paketmanager: $PKG"

install_pkg() {
    case $PKG in
        apt)    apt-get install -y -q "$@" ;;
        dnf)    dnf install -y -q "$@" ;;
        pacman) pacman -S --noconfirm --needed "$@" ;;
    esac
}

# Python 3.10+
if ! command -v python3 &>/dev/null; then
    info "Python3 wird installiert..."
    case $PKG in
        apt)    install_pkg python3 python3-pip python3-venv ;;
        dnf)    install_pkg python3 python3-pip ;;
        pacman) install_pkg python python-pip ;;
    esac
fi

PY=$(command -v python3)
PY_VER=$($PY -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PY -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PY -c "import sys; print(sys.version_info.minor)")

if [[ $PY_MAJOR -lt 3 || ($PY_MAJOR -eq 3 && $PY_MINOR -lt 10) ]]; then
    fail "Python 3.10+ erforderlich (gefunden: $PY_VER). Bitte manuell aktualisieren."
fi
ok "Python $PY_VER ($PY)"

# python3-venv sicherstellen (Debian/Ubuntu braucht das extra)
if ! $PY -m venv --help &>/dev/null 2>&1; then
    info "python3-venv wird installiert..."
    install_pkg python3-venv || true
fi

# git
if ! command -v git &>/dev/null; then
    info "Git wird installiert..."
    install_pkg git
fi
ok "Git $(git --version | awk '{print $3}')"

# ─── Virtuelle Umgebung ────────────────────────────────────────────────────────
header "2/5  Python-Umgebung einrichten"

if [[ -d "$VENV" ]]; then
    ok "Virtuelle Umgebung bereits vorhanden"
else
    info "Erstelle virtuelle Umgebung in $VENV ..."
    sudo -u "$RUN_USER" $PY -m venv "$VENV"
    ok "Virtuelle Umgebung erstellt"
fi

info "Installiere Python-Pakete..."
sudo -u "$RUN_USER" "$VENV/bin/pip" install --quiet --upgrade pip
sudo -u "$RUN_USER" "$VENV/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
ok "Pakete installiert"

# ─── Systemd-Service ───────────────────────────────────────────────────────────
header "3/5  Systemd-Service einrichten"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Divera247 → Shelly Schnittstelle
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${VENV}/bin/python ${APP_DIR}/app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

ok "Service-Datei erstellt: $SERVICE_FILE"

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
ok "Service aktiviert (startet automatisch beim Booten)"

# ─── Firewall (optional) ───────────────────────────────────────────────────────
header "4/5  Firewall"

if command -v ufw &>/dev/null; then
    if ufw status | grep -q "Status: active"; then
        ufw allow 5000/tcp &>/dev/null
        ok "ufw: Port 5000 freigegeben"
    else
        warn "ufw inaktiv – Port 5000 wurde nicht geöffnet"
    fi
elif command -v firewall-cmd &>/dev/null; then
    firewall-cmd --permanent --add-port=5000/tcp &>/dev/null
    firewall-cmd --reload &>/dev/null
    ok "firewalld: Port 5000 freigegeben"
else
    warn "Keine Firewall erkannt – Port 5000 bitte manuell freigeben falls nötig"
fi

# ─── Service starten ───────────────────────────────────────────────────────────
header "5/5  Service starten"

systemctl restart "$SERVICE_NAME"
sleep 2

if systemctl is-active --quiet "$SERVICE_NAME"; then
    ok "Service läuft"
else
    warn "Service konnte nicht gestartet werden. Log anzeigen mit:"
    echo "      sudo journalctl -u $SERVICE_NAME -n 30"
    exit 1
fi

# ─── Fertig ────────────────────────────────────────────────────────────────────
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')

echo ""
echo -e "${GREEN}${BOLD}Installation abgeschlossen!${NC}"
echo ""
echo -e "  Weboberfläche:   ${BOLD}http://localhost:5000${NC}"
[[ -n "$LOCAL_IP" ]] && \
echo -e "  Im Netzwerk:     ${BOLD}http://${LOCAL_IP}:5000${NC}"
echo ""
echo -e "  Standard-Login:  ${BOLD}admin / admin${NC}  (bitte sofort ändern!)"
echo ""
echo -e "  Service-Befehle:"
echo -e "    Status:    ${CYAN}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "    Neustart:  ${CYAN}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "    Stoppen:   ${CYAN}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "    Log:       ${CYAN}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo ""
