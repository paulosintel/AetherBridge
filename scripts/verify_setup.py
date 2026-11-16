#!/usr/bin/env python3
"""
AetherBridge Universal Diagnostic & Setup Verifier (Cross-Platform)
Verifies OmniRoute Gateway (direct AI provider), api_keys.env synchronization,
Claude CLI / Desktop wiring, persistent background daemon, and AetherBridge toolkit.
"""

import json
import os
import platform
import subprocess
import sys
import urllib.request

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8")
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
    print(f"{BOLD}[1/6] Verificando Gateway OmniRoute (Proveedor Directo :{port})...{RESET} ", end="")
    url = f"http://127.0.0.1:{port}/v1/models"
    token = resolve_token()

    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": "AetherBridge-Verifier"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            print(f"{GREEN}ONLINE y RESPONDIENDO (localhost:{port}){RESET}")
            if models:
                print(f"      Catálogo activo: {len(models)} modelos cloud disponibles vía AetherBridge.")
            return True
    except Exception as e:
        print(f"{YELLOW}OFFLINE o BLOQUEADO ({e}).{RESET}")
        print("      Tip: Inicia el servicio con 'python scripts/aether_service.py start'")
        return False


def check_api_keys_and_sync():
    print(f"\n{BOLD}[2/6] Verificando credenciales y sincronización de entorno...{RESET} ", end="")
    local_env = os.path.join(os.getcwd(), "api_keys.env")
    example_env = os.path.join(os.getcwd(), "api_keys.env.example")
    global_env = os.path.expanduser("~/.omniroute/.env")

    has_local = os.path.isfile(local_env)
    has_global = os.path.isfile(global_env)

    if has_local:
        count = 0
        with open(local_env, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        count += 1
        if has_global:
            print(f"{GREEN}SINCRONIZADO ({count} variables activas en local y global){RESET}")
        else:
            print(f"{YELLOW}LOCAL ACTIVO ({count} claves), pero falta sincronizar con ~/.omniroute/.env{RESET}")
            print("      Tip: Ejecuta 'python scripts/aether_service.py sync' para que OmniRoute reconozca tus claves.")
        return True
    elif os.path.isfile(example_env):
        print(f"{YELLOW}SOLO PLANTILLA DETECTADA (api_keys.env.example){RESET}")
        print("      Tip: Copia 'api_keys.env.example' como 'api_keys.env' y añade al menos 1 clave gratuita.")
        return False
    print(f"{RED}NO ENCONTRADO.{RESET}")
    return False


def check_daemon_autostart():
    print(f"\n{BOLD}[3/6] Verificando persistencia de servicio en segundo plano (Daemon)...{RESET} ", end="")
    system = platform.system()
    installed = False

    if system == "Darwin":
        plist = os.path.expanduser("~/Library/LaunchAgents/com.aetherbridge.omniroute.plist")
        if os.path.isfile(plist):
            installed = True
            print(f"{GREEN}CONFIGURADO (macOS LaunchAgent activo al encender o despertar){RESET}")
        else:
            print(f"{YELLOW}NO CONFIGURADO (Solo manual){RESET}")
            print("      Tip: Ejecuta 'python scripts/aether_service.py install-daemon' para que inicie solo con la Mac.")
    elif system == "Windows":
        startup_vbs = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AetherBridge_OmniRoute.vbs")
        if os.path.isfile(startup_vbs):
            installed = True
            print(f"{GREEN}CONFIGURADO (Inicio invisible en segundo plano con Windows){RESET}")
        else:
            print(f"{YELLOW}NO CONFIGURADO (Solo manual){RESET}")
            print("      Tip: Ejecuta 'python scripts\\aether_service.py install-daemon' para que inicie solo.")
    elif system == "Linux":
        service = os.path.expanduser("~/.config/systemd/user/aetherbridge-omniroute.service")
        if os.path.isfile(service):
            installed = True
            print(f"{GREEN}CONFIGURADO (systemd user service activo){RESET}")
        else:
            print(f"{YELLOW}NO CONFIGURADO (Solo manual){RESET}")
            print("      Tip: Ejecuta 'python scripts/aether_service.py install-daemon'")
    return installed


def check_claude_clients():
    port = os.environ.get("OMNIROUTE_PORT", "20128")
    print(f"\n{BOLD}[4/6] Verificando cableado de Claude CLI y Claude Desktop...{RESET} ", end="")
    home = os.path.expanduser("~")
    settings_file = os.path.join(home, ".claude", "settings.json")
    cli_ok = False

    if os.path.isfile(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "ANTHROPIC_BASE_URL" in content and f":{port}" in content:
                    cli_ok = True
        except Exception:
            pass
    if not cli_ok and os.environ.get("ANTHROPIC_BASE_URL"):
        cli_ok = True

    desktop_ok = False
    system = platform.system()
    if system == "Darwin":
        desktop_conf = os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json")
        if os.path.isfile(desktop_conf):
            try:
                with open(desktop_conf, "r", encoding="utf-8") as f:
                    if "omniroute_mcp_bridge" in f.read():
                        desktop_ok = True
            except Exception:
                pass
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        desktop_conf = os.path.join(appdata, "Claude", "claude_desktop_config.json")
        if os.path.isfile(desktop_conf):
            try:
                with open(desktop_conf, "r", encoding="utf-8") as f:
                    if "omniroute_mcp_bridge" in f.read():
                        desktop_ok = True
            except Exception:
                pass

    if cli_ok and desktop_ok:
        print(f"{GREEN}CONFIGURADO (Claude CLI + Claude Desktop MCP -> OmniRoute){RESET}")
    elif cli_ok:
        print(f"{GREEN}CONFIGURADO (Claude CLI -> localhost:{port}){RESET}")
    else:
        print(f"{YELLOW}SIN CONFIGURAR.{RESET}")
        print(f"      Tip: Ejecuta 'python scripts/aether_service.py sync' para auto-configurar Claude CLI.")
    return cli_ok


def check_ollama_optional():
    print(f"\n{BOLD}[5/6] Verificando nodo local Ollama (Opcional)...{RESET} ", end="")
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/tags")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AetherBridge-Verifier"})
        with urllib.request.urlopen(req, timeout=1.2) as resp:
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
    print(f"\n{BOLD}[6/6] Verificando suite de scripts AetherBridge en scripts/...{RESET} ", end="")
    required = ["aether_service.py", "gemini_sandwich.py", "aether_consult.py", "auto_update_catalog.py", "omniroute_mcp_bridge.js"]
    missing = [r for r in required if not os.path.isfile(os.path.join("scripts", r))]
    if not missing:
        print(f"{GREEN}SUITE COMPLETA (Service Daemon, Sandwich, Consult, MCP Bridge, AutoUpdate){RESET}")
        return True
    print(f"{YELLOW}Faltan scripts: {', '.join(missing)}{RESET}")
    return False


def main():
    print_header()
    check_omniroute()
    check_api_keys_and_sync()
    check_daemon_autostart()
    check_claude_clients()
    check_ollama_optional()
    check_scripts()
    print(f"\n{CYAN}================================================================={RESET}")
    print(f"{GREEN}  Diagnóstico finalizado. Para iniciar el Gateway automáticamente: {RESET}")
    python_cmd = "python" if platform.system() == "Windows" else "python3"
    print(f"  {python_cmd} scripts/aether_service.py start")
    print(f"  {python_cmd} scripts/aether_service.py install-daemon")
    print(f"{CYAN}================================================================={RESET}\n")


if __name__ == "__main__":
    main()
