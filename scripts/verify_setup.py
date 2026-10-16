#!/usr/bin/env python3
"""
AetherBridge Universal Diagnostic & Setup Verifier (Cross-Platform)
Compatible with Windows, macOS, and Linux.
Verifies Ollama, OmniRoute Gateway, api_keys.env, Claude CLI settings, and script toolkit.
"""

import os
import sys
import json
import platform
import urllib.request
import urllib.error
import subprocess

# ANSI color codes (supported natively in modern Windows Terminal, macOS, and Linux)
if platform.system() == "Windows":
    # Enable ANSI escape sequences on Windows consoles if needed
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header():
    os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"
    print(f"{CYAN}================================================================={RESET}")
    print(f"{CYAN}   🌉 AETHERBRIDGE: DIAGNÓSTICO UNIVERSAL DE INFRAESTRUCTURA      {RESET}")
    print(f"{CYAN}   Sistema Detectado: {BOLD}{os_name}{RESET}")
    print(f"{CYAN}   Democratización de Modelos Cloud Gratuitos & Nodos Locales    {RESET}")
    print(f"{CYAN}================================================================={RESET}\n")

def check_ollama():
    print(f"{BOLD}[1/5] Verificando servicio de Ollama (Resiliencia Local)...{RESET} ", end="")
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/tags")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AetherBridge-Verifier"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            print(f"{GREEN}ACTIVO (localhost:11434){RESET}")
            if models:
                print("      Modelos locales listos en Ollama:")
                for m in models:
                    print(f"      - {m}")
            else:
                print(f"      {YELLOW}(No hay modelos descargados todavía. Sugerencia: 'ollama pull llama3.2'){RESET}")
            return True
    except Exception:
        # Check if ollama binary is installed
        ollama_bin = "ollama.exe" if platform.system() == "Windows" else "ollama"
        installed = False
        try:
            res = subprocess.run([ollama_bin, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0:
                installed = True
        except FileNotFoundError:
            pass

        if installed:
            print(f"{YELLOW}INSTALADO pero NO ACTIVO.{RESET}")
            print("      Tip: Abre la aplicación de Ollama o ejecuta 'ollama serve' en una terminal.")
        else:
            print(f"{RED}NO INSTALADO.{RESET}")
            if platform.system() == "Windows":
                print("      Tip Windows: Ejecuta 'winget install Ollama.Ollama' o descarga desde https://ollama.com/download/windows")
            elif platform.system() == "Darwin":
                print("      Tip macOS: brew install ollama")
            else:
                print("      Tip Linux: curl -fsSL https://ollama.com/install.sh | sh")
        return False

def check_api_keys():
    print(f"\n{BOLD}[2/5] Verificando credenciales 'api_keys.env'...{RESET} ", end="")
    env_path = os.path.join(os.getcwd(), "api_keys.env")
    example_path = os.path.join(os.getcwd(), "api_keys.env.example")

    if os.path.isfile(env_path):
        count = 0
        with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    val = line.split("=", 1)[1].strip()
                    if val and val != '""' and val != "''":
                        count += 1
        print(f"{GREEN}ENCONTRADO ({count} claves/variables activas detectadas){RESET}")
        return True
    elif os.path.isfile(example_path):
        print(f"{YELLOW}SOLO PLANTILLA DETECTADA (api_keys.env.example){RESET}")
        print("      Tip: Copia 'api_keys.env.example' como 'api_keys.env' y añade al menos 1 clave gratuita.")
        return False
    else:
        print(f"{RED}NO ENCONTRADO.{RESET}")
        return False

def check_omniroute():
    port = os.environ.get("OMNIROUTE_PORT", "20128")
    print(f"\n{BOLD}[3/5] Verificando Gateway OmniRoute en puerto {port}...{RESET} ", end="")
    url = f"http://127.0.0.1:{port}/v1/models"
    token = os.environ.get("OMNIROUTE_API_KEY", os.environ.get("OMNIROUTE_LOCAL_TOKEN", "sk-aetherbridge"))

    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "AetherBridge-Verifier"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            print(f"{GREEN}ONLINE y RESPONDIENDO (localhost:{port}){RESET}")
            if models:
                print(f"      Catálogo activo: {len(models)} modelos disponibles vía AetherBridge.")
            return True
    except Exception:
        print(f"{YELLOW}OFFLINE o NO RESPONDE.{RESET}")
        print(f"      Tip: Inicia el motor con 'omniroute serve' o mediante el Prompt Maestro.")
        return False

def check_claude_cli():
    print(f"\n{BOLD}[4/5] Verificando cableado de Claude CLI (Claude Code)...{RESET} ", end="")
    home = os.path.expanduser("~")
    settings_file = os.path.join(home, ".claude", "settings.json")
    
    # Check settings.json
    configured = False
    if os.path.isfile(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "ANTHROPIC_BASE_URL" in content:
                    print(f"{GREEN}CONFIGURADO en {settings_file}{RESET}")
                    configured = True
        except Exception:
            pass

    if not configured:
        env_url = os.environ.get("ANTHROPIC_BASE_URL")
        if env_url:
            print(f"{GREEN}ACTIVO vía variable de entorno: {env_url}{RESET}")
            configured = True
        else:
            print(f"{YELLOW}SIN CONFIGURAR.{RESET}")
            if platform.system() == "Windows":
                print("      Tip Windows (PowerShell):")
                print("        [System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', 'http://localhost:20128', 'User')")
                print("        [System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'sk-aetherbridge', 'User')")
            else:
                print("      Tip macOS/Linux: Define ANTHROPIC_BASE_URL=http://localhost:20128 en tu ~/.zshrc o ~/.claude/settings.json")
    return configured

def check_scripts():
    print(f"\n{BOLD}[5/5] Verificando suite de scripts AetherBridge en scripts/...{RESET} ", end="")
    required = [
        "gemini_sandwich.py",
        "aether_consult.py",
        "auto_update_catalog.py",
        "omniroute_mcp_bridge.js"
    ]
    missing = []
    for r in required:
        p = os.path.join("scripts", r)
        if not os.path.isfile(p):
            missing.append(r)
    
    if not missing:
        print(f"{GREEN}SUITE COMPLETA (Sandwich, Consult, MCP Bridge, AutoUpdate){RESET}")
        return True
    else:
        print(f"{YELLOW}Faltan scripts: {', '.join(missing)}{RESET}")
        return False

def main():
    print_header()
    check_ollama()
    check_api_keys()
    check_omniroute()
    check_claude_cli()
    check_scripts()
    print(f"\n{CYAN}================================================================={RESET}")
    print(f"{GREEN}  Diagnóstico finalizado. Para consultas rápidas:                {RESET}")
    python_cmd = "python" if platform.system() == "Windows" else "python3"
    print(f"  {python_cmd} scripts/aether_consult.py -m fast \"¿Hola Mundo?\"")
    print(f"{CYAN}================================================================={RESET}\n")

if __name__ == "__main__":
    main()
