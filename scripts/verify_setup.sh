#!/usr/bin/env bash
# ==============================================================================
# AETHERBRIDGE: SCRIPT DE VERIFICACIÓN Y DIAGNÓSTICO DEL ECOSISTEMA
# Proveedor Directo OmniRoute Engine + Claude CLI / Claude Desktop / Codex
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=================================================================${NC}"
echo -e "${CYAN}   🌉 AETHERBRIDGE: DIAGNÓSTICO DE INFRAESTRUCTURA DE IA         ${NC}"
echo -e "${CYAN}   Proveedores Directos Cloud vía OmniRoute - AetherBridge       ${NC}"
echo -e "${CYAN}=================================================================${NC}"

PORT=${OMNIROUTE_PORT:-20128}
TOKEN="${OMNIROUTE_API_KEY:-}"
if [ -z "$TOKEN" ] && [ -f "${HOME}/.omniroute/.env" ]; then
    TOKEN=$(grep -E '^OMNIROUTE_API_KEY=' "${HOME}/.omniroute/.env" | cut -d'=' -f2 | tr -d '"'\'' ')
fi
if [ -z "$TOKEN" ] && [ -f "api_keys.env" ]; then
    TOKEN=$(grep -E '^OMNIROUTE_LOCAL_TOKEN=' api_keys.env | cut -d'=' -f2 | tr -d '"'\'' ')
fi
TOKEN="${TOKEN:-omniroute-secret-key-local}"

# 1. Verificar estado del Gateway OmniRoute (Motor central)
echo -ne "\n[1/5] Verificando Gateway OmniRoute en puerto ${PORT}... "
if curl -s -H "Authorization: Bearer ${TOKEN}" http://localhost:${PORT}/v1/models | grep -q '"data"'; then
    echo -e "${GREEN}ONLINE y RESPONDIENDO (localhost:${PORT})${NC}"
    MODELS_COUNT=$(curl -s -H "Authorization: Bearer ${TOKEN}" http://localhost:${PORT}/v1/models 2>/dev/null | grep -o '"id":' | wc -l | tr -d ' ')
    if [ "$MODELS_COUNT" -gt 0 ]; then
        echo -e "      Catálogo activo: ${MODELS_COUNT} modelos disponibles vía OmniRoute - AetherBridge."
    fi
else
    echo -e "${YELLOW}OFFLINE o NO RESPONDE.${NC}"
    echo -e "      Tip: Inicia el motor con 'omniroute serve'."
fi

# 2. Verificar archivo de claves API
echo -ne "\n[2/5] Verificando credenciales 'api_keys.env'... "
if [ -f "api_keys.env" ]; then
    KEYS_COUNT=$(grep -v '^#' api_keys.env | grep -v '^[[:space:]]*$' | grep -c '=')
    echo -e "${GREEN}ENCONTRADO (${KEYS_COUNT} claves/variables detectadas)${NC}"
elif [ -f "api_keys.env.example" ]; then
    echo -e "${YELLOW}SOLO PLANTILLA DETECTADA (api_keys.env.example)${NC}"
else
    echo -e "${RED}NO ENCONTRADO.${NC}"
fi

# 3. Verificar configuración para Claude CLI y Claude Desktop
echo -ne "\n[3/5] Verificando cableado de Claude CLI y Claude Desktop... "
SETTINGS_FILE="${HOME}/.claude/settings.json"
DESKTOP_META="${HOME}/Library/Application Support/Claude-3p/configLibrary/_meta.json"
CLI_OK=false
DESKTOP_OK=false

if [ -f "$SETTINGS_FILE" ] && grep -q "ANTHROPIC_BASE_URL" "$SETTINGS_FILE"; then
    CLI_OK=true
elif [ -n "$ANTHROPIC_BASE_URL" ]; then
    CLI_OK=true
fi

if [ -f "$DESKTOP_META" ] && grep -q "appliedId" "$DESKTOP_META"; then
    DESKTOP_OK=true
fi

if [ "$CLI_OK" = true ] && [ "$DESKTOP_OK" = true ]; then
    echo -e "${GREEN}CONFIGURADO (Claude CLI + Claude Desktop 3P Gateway)${NC}"
elif [ "$CLI_OK" = true ]; then
    echo -e "${GREEN}CONFIGURADO (Claude CLI -> localhost:${PORT})${NC}"
else
    echo -e "${YELLOW}SIN CONFIGURAR.${NC}"
fi

# 4. Verificar si Ollama está instalado (Opcional)
echo -ne "\n[4/5] Verificando nodo local Ollama (Opcional)... "
if command -v ollama >/dev/null 2>&1 && curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${GREEN}ACTIVO (localhost:11434)${NC}"
else
    echo -e "${CYAN}OPCIONAL — No activo (operando 100% vía OmniRoute Cloud Directo)${NC}"
fi

# 5. Verificar scripts auxiliares de AetherBridge
echo -ne "\n[5/5] Verificando suite de scripts AetherBridge en scripts/... "
SCRIPTS_OK=true
for f in scripts/gemini_sandwich.py scripts/aether_consult.py scripts/omni_consult.py scripts/omniroute_mcp_bridge.js; do
    if [ ! -f "$f" ]; then
        SCRIPTS_OK=false
    fi
done

if [ "$SCRIPTS_OK" = true ]; then
    echo -e "${GREEN}SUITE COMPLETA (Sandwich, Consult, MCP Bridge)${NC}"
else
    echo -e "${YELLOW}Faltan algunos scripts en la carpeta scripts/${NC}"
fi

echo -e "\n${CYAN}=================================================================${NC}"
echo -e "${GREEN}  Diagnóstico finalizado con éxito.                              ${NC}"
echo -e "${CYAN}=================================================================${NC}\n"
