#!/usr/bin/env bash
# ==============================================================================
# AETHERBRIDGE: SCRIPT DE VERIFICACIÓN Y DIAGNÓSTICO DEL ECOSISTEMA
# Ollama + OmniRoute Engine + Claude CLI / Codex
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=================================================================${NC}"
echo -e "${CYAN}   🌉 AETHERBRIDGE: DIAGNÓSTICO DE INFRAESTRUCTURA DE IA         ${NC}"
echo -e "${CYAN}   Democratización de Modelos Cloud Gratuitos & Nodos Locales    ${NC}"
echo -e "${CYAN}=================================================================${NC}"

# 1. Verificar si Ollama está instalado y activo
echo -ne "\n[1/5] Verificando servicio de Ollama (Resiliencia Local)... "
if command -v ollama >/dev/null 2>&1; then
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${GREEN}ACTIVO (localhost:11434)${NC}"
        echo -e "      Modelos locales listos en Ollama:"
        ollama list 2>/dev/null | awk 'NR>1 {print "      - " $1}'
    else
        echo -e "${YELLOW}INSTALADO pero NO ACTIVO.${NC}"
        echo -e "      Tip: Inicia Ollama con 'ollama serve' o abre la aplicación Ollama."
    fi
else
    echo -e "${RED}NO INSTALADO.${NC}"
    echo -e "      Tip Windows: winget install Ollama.Ollama | macOS: brew install ollama | Linux: curl -fsSL https://ollama.com/install.sh | sh"
fi

# 2. Verificar archivo de claves API
echo -ne "\n[2/5] Verificando credenciales 'api_keys.env'... "
if [ -f "api_keys.env" ]; then
    KEYS_COUNT=$(grep -v '^#' api_keys.env | grep -v '^[[:space:]]*$' | grep -c '=')
    echo -e "${GREEN}ENCONTRADO (${KEYS_COUNT} claves/variables detectadas)${NC}"
elif [ -f "api_keys.env.example" ]; then
    echo -e "${YELLOW}SOLO PLANTILLA DETECTADA (api_keys.env.example)${NC}"
    echo -e "      Tip: Copia 'api_keys.env.example' a 'api_keys.env' y añade al menos 1 clave gratuita."
else
    echo -e "${RED}NO ENCONTRADO.${NC}"
fi

# 3. Verificar estado del Gateway OmniRoute (Motor central)
PORT=${OMNIROUTE_PORT:-20128}
echo -ne "\n[3/5] Verificando Gateway OmniRoute en puerto ${PORT}... "
if curl -s http://localhost:${PORT}/v1/models >/dev/null 2>&1 || curl -s http://localhost:${PORT}/health >/dev/null 2>&1; then
    echo -e "${GREEN}ONLINE y RESPONDIENDO (localhost:${PORT})${NC}"
    TOKEN="${OMNIROUTE_API_KEY:-}"
    if [ -z "$TOKEN" ] && [ -f "api_keys.env" ]; then
        TOKEN=$(grep -E '^OMNIROUTE_LOCAL_TOKEN=' api_keys.env | cut -d'=' -f2 | tr -d '"'\'' ')
    fi
    if [ -z "$TOKEN" ] && [ -f "${HOME}/.omniroute/.env" ]; then
        TOKEN=$(grep -E '^OMNIROUTE_API_KEY=' "${HOME}/.omniroute/.env" | cut -d'=' -f2 | tr -d '"'\'' ')
    fi
    TOKEN="${TOKEN:-sk-115537bd46614765-e41eb2-08652b97}"
    MODELS_COUNT=$(curl -s -H "Authorization: Bearer ${TOKEN}" http://localhost:${PORT}/v1/models 2>/dev/null | grep -o '"id":' | wc -l | tr -d ' ')
    if [ "$MODELS_COUNT" -gt 0 ]; then
        echo -e "      Catálogo activo: ${MODELS_COUNT} modelos disponibles vía AetherBridge."
    fi
else
    echo -e "${YELLOW}OFFLINE o NO RESPONDE.${NC}"
    echo -e "      Tip: Inicia el motor con 'omniroute serve' o mediante el Prompt Maestro."
fi

# 4. Verificar configuración para Claude CLI (Claude Code)
echo -ne "\n[4/5] Verificando cableado de Claude CLI... "
SETTINGS_FILE="${HOME}/.claude/settings.json"
CLAUDE_CONFIGURED=false

if [ -f "$SETTINGS_FILE" ]; then
    if grep -q "ANTHROPIC_BASE_URL" "$SETTINGS_FILE"; then
        echo -e "${GREEN}CONFIGURADO en ~/.claude/settings.json${NC}"
        CLAUDE_CONFIGURED=true
    fi
fi

if [ "$CLAUDE_CONFIGURED" = false ]; then
    if [ -n "$ANTHROPIC_BASE_URL" ]; then
        echo -e "${GREEN}ACTIVO vía variable de entorno: $ANTHROPIC_BASE_URL${NC}"
    else
        echo -e "${YELLOW}SIN CONFIGURAR.${NC}"
        echo -e "      Tip: Define ANTHROPIC_BASE_URL=http://localhost:${PORT} en tu ~/.zshrc o ~/.claude/settings.json"
    fi
fi

# 5. Verificar scripts auxiliares de AetherBridge
echo -ne "\n[5/5] Verificando suite de scripts AetherBridge en scripts/... "
SCRIPTS_OK=true
for f in scripts/gemini_sandwich.py scripts/omni_consult.py scripts/omniroute_mcp_bridge.js; do
    if [ ! -f "$f" ]; then
        SCRIPTS_OK=false
    fi
done

if [ "$SCRIPTS_OK" = true ]; then
    echo -e "${GREEN}SUITE COMPLETA (Sandwich Engine, Consult CLI, MCP Bridge)${NC}"
else
    echo -e "${YELLOW}Faltan algunos scripts en la carpeta scripts/${NC}"
fi

echo -e "\n${CYAN}=================================================================${NC}"
echo -e "${GREEN}  Diagnóstico finalizado con éxito.                              ${NC}"
echo -e "${CYAN}=================================================================${NC}\n"
