#!/usr/bin/env bash
# ==============================================================================
# 🌉 AETHERBRIDGE: INICIADOR UNIVERSAL PARA MACOS (MACBOOK & MAC MINI)
# Doble clic en Finder o ejecutable desde Terminal
# ==============================================================================

set -e
cd "$(dirname "$0")"

# Asegurar rutas de Homebrew (Apple Silicon + Intel) y Node en PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}=================================================================${NC}"
echo -e "${CYAN}   🌉 AETHERBRIDGE: INICIADOR AUTOMÁTICO PARA MACOS              ${NC}"
echo -e "${CYAN}   Zero-Cost Frontier AI Gateway & Resilient Infrastructure      ${NC}"
echo -e "${CYAN}=================================================================${NC}\n"

# 1. Comprobar Python
PYTHON_CMD="python3"
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
    echo -e "${YELLOW}[ERROR] python3 no encontrado en el sistema.${NC}"
    exit 1
fi

# 2. Sincronizar credenciales
echo -e "[1/3] Sincronizando credenciales (api_keys.env -> ~/.omniroute/.env)..."
$PYTHON_CMD scripts/aether_service.py sync
echo ""

# 3. Comprobar e instalar LaunchAgent permanente para MacBook / Mac mini
PLIST_FILE="${HOME}/Library/LaunchAgents/com.aetherbridge.omniroute.plist"
if [ ! -f "$PLIST_FILE" ]; then
    echo -e "[2/3] Configurando demonio de persistencia macOS (LaunchAgent)..."
    echo -e "      (Garantiza que OmniRoute no se apague al cerrar la tapa de tu MacBook o reiniciar)"
    $PYTHON_CMD scripts/aether_service.py install-daemon
else
    echo -e "[2/3] Levantando Gateway OmniRoute en segundo plano..."
    $PYTHON_CMD scripts/aether_service.py start
fi
echo ""

# 4. Diagnóstico de Salud
echo -e "[3/3] Verificando salud del ecosistema..."
$PYTHON_CMD scripts/verify_setup.py

echo -e "\n${CYAN}=================================================================${NC}"
echo -e "¿Qué deseas hacer ahora?"
echo -e "1) Abrir Claude CLI (Claude Code) conectado a AetherBridge"
echo -e "2) Probar consulta rápida (LPU Ultra-Rápido)"
echo -e "3) Salir (El servidor seguirá activo en segundo plano)"
echo -e "${CYAN}=================================================================${NC}"
read -r -p "Selecciona una opción [1]: " OPT

OPT="${OPT:-1}"

if [ "$OPT" = "2" ]; then
    echo ""
    $PYTHON_CMD scripts/aether_consult.py -m fast "¿Hola, estás listo para programar?"
    echo ""
    read -r -p "Presiona Enter para finalizar..."
    exit 0
fi

if [ "$OPT" = "1" ]; then
    if command -v claude >/dev/null 2>&1; then
        echo -e "\n${GREEN}Iniciando Claude CLI...${NC}"
        claude
    else
        echo -e "\n${YELLOW}[Aviso] Claude CLI no está instalado globalmente.${NC}"
        echo -e "Puedes instalarlo con: npm install -g @anthropic-ai/claude-code"
        echo -e "O usar el gateway con Codex, Antigravity o tus scripts locales.\n"
        read -r -p "Presiona Enter para finalizar..."
    fi
fi
