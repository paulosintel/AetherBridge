#!/usr/bin/env python3
"""
AetherBridge Universal Diagnostic & Setup Verifier (Cross-Platform)
Verifies OmniRoute Gateway (direct AI provider), api_keys.env, Claude CLI / Desktop,
optional Ollama local engine, and AetherBridge script toolkit.
"""

import json
import os
import platform
import subprocess
import urllib.request

if platform.system() == "Windows":
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


def _read_env_value(filepath: str, keys: tuple) -> str:
    if not os.path.isfile(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() in keys:
                    val = v.strip().strip('"').strip("'")
                    if val:
                        return val
    except Exception:
        pass
    return ""


def resolve_token() -> str:
    for env_key in ("OMNIROUTE_API_KEY", "OMNIROUTE_TOKEN", "OMNIROUTE_LOCAL_TOKEN"):
        val = os.environ.get(env_key, "").strip()
        if val:
            return val
    for candidate in (
        os.path.expanduser("~/.omniroute/.env"),
        os.path.join(os.getcwd(), "api_keys.env"),
    ):
        val = _read_env_value(candidate, ("OMNIROUTE_API_KEY", "OMNIROUTE_LOCAL_TOKEN"))
        if val:
            return val
    return "omniroute-secret-key-local"


def print_header():
    os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"
    print(f"{CYAN}================================================================={RESET}")
    print(f"{CYAN}   🌉 AETHERBRIDGE: DIAGNÓSTICO UNIVERSAL DE INFRAESTRUCTURA      {RESET}")
    print(f"{CYAN}   Sistema Detectado: {BOLD}{os_name}{RESET}")
    print(f"{CYAN}   Proveedores Directos de IA vía OmniRoute - AetherBridge       {RESET}")
    print(f"{CYAN}================================================================={RESET}\n")


def check_omniroute():
    port = os.environ.get("OMNIROUTE_PORT", "20128")
    print(f"{BOLD}[1/5] Verificando Gateway OmniRoute (Proveedor Directo :{port})...{RESET} ", end="")
    url = f"http://127.0.0.1:{port}/v1/models"
    token = resolve_token()

    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "AetherBridge-Verifier"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            print(f"{GREEN}ONLINE y RESPONDIENDO (localhost:{port}){RESET}")
            if models:
                print(f"      Catálogo activo: {len(models)} modelos cloud disponibles vía AetherBridge.")
            return True
    except Exception as e:
        print(f"{YELLOW}OFFLINE o BLOQUEADO ({e}).{RESET}")
        print("      Tip: Inicia el motor con 'omniroute serve' o verifica la red local.")
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
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        count += 1
        print(f"{GREEN}ENCONTRADO ({count} claves/variables activas detectadas){RESET}")
        return True
    if os.path.isfile(example_path):
        print(f"{YELLOW}SOLO PLANTILLA DETECTADA (api_keys.env.example){RESET}")
        print("      Tip: Copia 'api_keys.env.example' como 'api_keys.env' y añade al menos 1 clave gratuita.")
        return False
    print(f"{RED}NO ENCONTRADO.{RESET}")
    return False


def check_claude_clients():
    print(f"\n{BOLD}[3/5] Verificando cableado de Claude CLI y Claude Desktop...{RESET} ", end="")
    home = os.path.expanduser("~")
    settings_file = os.path.join(home, ".claude", "settings.json")
    cli_ok = False

    if os.path.isfile(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                if "ANTHROPIC_BASE_URL" in f.read():
                    cli_ok = True
        except Exception:
            pass
    if not cli_ok and os.environ.get("ANTHROPIC_BASE_URL"):
        cli_ok = True

    desktop_ok = False
    if platform.system() == "Darwin":
        meta_path = os.path.join(home, "Library", "Application Support", "Claude-3p", "configLibrary", "_meta.json")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    if meta.get("appliedId"):
                        desktop_ok = True
            except Exception:
                pass

    if cli_ok and desktop_ok:
        print(f"{GREEN}CONFIGURADO (Claude CLI + Claude Desktop 3P Gateway -> OmniRoute){RESET}")
    elif cli_ok:
        print(f"{GREEN}CONFIGURADO (Claude CLI -> OmniRoute){RESET}")
    else:
        print(f"{YELLOW}SIN CONFIGURAR.{RESET}")
        print("      Tip: Define ANTHROPIC_BASE_URL=http://localhost:20128 en ~/.claude/settings.json")
    return cli_ok


def check_ollama_optional():
    print(f"\n{BOLD}[4/5] Verificando nodo local Ollama (Opcional)...{RESET} ", end="")
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/tags")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AetherBridge-Verifier"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            print(f"{GREEN}ACTIVO (localhost:11434, {len(models)} modelos locales){RESET}")
            return True
    except Exception:
        ollama_bin = "ollama.exe" if platform.system() == "Windows" else "ollama"
        installed = False
        try:
            res = subprocess.run([ollama_bin, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            installed = res.returncode == 0
        except FileNotFoundError:
            pass
        if installed:
            print(f"{CYAN}INSTALADO pero INACTIVO (operando vía OmniRoute Cloud){RESET}")
        else:
            print(f"{CYAN}OPCIONAL — No instalado (operando 100% vía OmniRoute Cloud Directo){RESET}")
        return False


def check_scripts():
    print(f"\n{BOLD}[5/5] Verificando suite de scripts AetherBridge en scripts/...{RESET} ", end="")
    required = ["gemini_sandwich.py", "aether_consult.py", "auto_update_catalog.py", "omniroute_mcp_bridge.js"]
    missing = [r for r in required if not os.path.isfile(os.path.join("scripts", r))]
    if not missing:
        print(f"{GREEN}SUITE COMPLETA (Sandwich, Consult, MCP Bridge, AutoUpdate){RESET}")
        return True
    print(f"{YELLOW}Faltan scripts: {', '.join(missing)}{RESET}")
    return False


def main():
    print_header()
    check_omniroute()
    check_api_keys()
    check_claude_clients()
    check_ollama_optional()
    check_scripts()
    print(f"\n{CYAN}================================================================={RESET}")
    print(f"{GREEN}  Diagnóstico finalizado. Para consultas rápidas:                {RESET}")
    python_cmd = "python" if platform.system() == "Windows" else "python3"
    print(f"  {python_cmd} scripts/aether_consult.py -m sonnet \"¿Hola Mundo?\"")
    print(f"{CYAN}================================================================={RESET}\n")


if __name__ == "__main__":
    main()
