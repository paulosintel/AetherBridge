#!/usr/bin/env python3
"""
AetherBridge Universal Service & Daemon Manager (Cross-Platform)
Manages OmniRoute lifecycle, environment synchronization, and persistent background daemons
across macOS (LaunchAgents), Windows (Task Scheduler / Background Startup), and Linux (systemd).
"""

import argparse
import glob
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
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

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_ENV_PATH = os.path.join(REPO_ROOT, "api_keys.env")
LOCAL_ENV_EXAMPLE = os.path.join(REPO_ROOT, "api_keys.env.example")
GLOBAL_OMNI_DIR = os.path.expanduser("~/.omniroute")
GLOBAL_ENV_PATH = os.path.join(GLOBAL_OMNI_DIR, ".env")
LOG_DIR = os.path.join(GLOBAL_OMNI_DIR, "logs")
OUT_LOG = os.path.join(LOG_DIR, "omniroute.log")
ERR_LOG = os.path.join(LOG_DIR, "omniroute.err.log")
DEFAULT_PORT = 20128
DEFAULT_TOKEN = "omniroute-secret-key-local"

LAUNCHD_PLIST_ID = "com.aetherbridge.omniroute"
LAUNCHD_PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{LAUNCHD_PLIST_ID}.plist")
WIN_TASK_NAME = "AetherBridge_OmniRoute_Daemon"
WIN_STARTUP_DIR = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")


def parse_env_file(filepath: str) -> dict:
    env_vars = {}
    if not os.path.isfile(filepath):
        return env_vars
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k:
                    env_vars[k] = v
    except Exception as e:
        print(f"{YELLOW}[Env] Advertencia leyendo {filepath}: {e}{RESET}")
    return env_vars


def write_env_file(filepath: str, env_vars: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Generated automatically by AetherBridge Service Manager\n")
            f.write(f"# Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for k in sorted(env_vars.keys()):
                f.write(f'{k}="{env_vars[k]}"\n')
        return True
    except (PermissionError, OSError) as e:
        print(f"{YELLOW}[Env] Aviso: No se pudo escribir en {filepath} ({e}). Continuará con variables en memoria.{RESET}")
        return False


def sync_environments() -> dict:
    """
    Synchronizes api_keys.env into ~/.omniroute/.env ensuring the OmniRoute engine
    receives all cloud keys, tokens, and correct port bindings across any machine.
    """
    try:
        os.makedirs(GLOBAL_OMNI_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
    except (PermissionError, OSError):
        pass

    # 1. Read existing global ~/.omniroute/.env
    global_vars = parse_env_file(GLOBAL_ENV_PATH)

    # 2. Read local api_keys.env (or copy from example if missing)
    if not os.path.isfile(LOCAL_ENV_PATH) and os.path.isfile(LOCAL_ENV_EXAMPLE):
        try:
            shutil.copy(LOCAL_ENV_EXAMPLE, LOCAL_ENV_PATH)
            print(f"{CYAN}[Sync] Se creó 'api_keys.env' a partir de la plantilla.{RESET}")
        except Exception:
            pass

    local_vars = parse_env_file(LOCAL_ENV_PATH)

    # 3. Merge: Local repository keys have priority, but preserve any extra global keys
    merged = dict(global_vars)
    for k, v in local_vars.items():
        if v or k not in merged:
            merged[k] = v

    # 4. Enforce mandatory OmniRoute configuration defaults
    port = merged.get("OMNIROUTE_PORT") or merged.get("PORT") or str(DEFAULT_PORT)
    token = merged.get("OMNIROUTE_API_KEY") or merged.get("OMNIROUTE_LOCAL_TOKEN") or DEFAULT_TOKEN

    merged["PORT"] = port
    merged["OMNIROUTE_PORT"] = port
    merged["OMNIROUTE_API_KEY"] = token
    merged["OMNIROUTE_LOCAL_TOKEN"] = token
    merged["REQUIRE_API_KEY"] = "true"
    merged["BIND_HOST"] = "0.0.0.0"

    # Save to global ~/.omniroute/.env
    write_env_file(GLOBAL_ENV_PATH, merged)

    # Also ensure local api_keys.env has the token & port
    if os.path.isfile(LOCAL_ENV_PATH):
        if not local_vars.get("OMNIROUTE_PORT") or not local_vars.get("OMNIROUTE_LOCAL_TOKEN"):
            local_vars["OMNIROUTE_PORT"] = port
            local_vars["OMNIROUTE_LOCAL_TOKEN"] = token
            write_env_file(LOCAL_ENV_PATH, local_vars)

    # Automatically patch Claude CLI settings (~/.claude/settings.json)
    patch_claude_cli_settings(port, token)

    return merged


def patch_claude_cli_settings(port: str, token: str):
    settings_dir = os.path.expanduser("~/.claude")
    settings_file = os.path.join(settings_dir, "settings.json")
    try:
        os.makedirs(settings_dir, exist_ok=True)
        data = {}
        if os.path.isfile(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        env_block = data.get("env", {})
        env_block["ANTHROPIC_BASE_URL"] = f"http://localhost:{port}"
        env_block["ANTHROPIC_AUTH_TOKEN"] = token
        data["env"] = env_block
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        pass


def find_executable(name: str, extra_paths=None) -> str:
    """Cross-platform binary lookup handling Windows .cmd/.exe and Mac homebrew/nvm."""
    search_paths = []
    if extra_paths:
        search_paths.extend(extra_paths)

    system = platform.system()
    if system == "Darwin":
        search_paths.extend([
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/usr/bin",
            os.path.expanduser("~/.nvm/versions/node/*/bin"),
        ])
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        search_paths.extend([
            os.path.join(appdata, "npm"),
            os.path.join(localappdata, "Programs", "nodejs"),
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "nodejs"),
        ])

    # Direct which
    found = shutil.which(name)
    if found:
        return os.path.abspath(found)

    # Windows extensions
    extensions = [".cmd", ".exe", ".bat", ""] if system == "Windows" else [""]
    for p in search_paths:
        if "*" in p:
            expanded = glob.glob(p)
            for exp in expanded:
                for ext in extensions:
                    target = os.path.join(exp, name + ext)
                    if os.path.isfile(target):
                        return os.path.abspath(target)
        else:
            for ext in extensions:
                target = os.path.join(p, name + ext)
                if os.path.isfile(target):
                    return os.path.abspath(target)

    return ""


def get_omniroute_bin() -> str:
    omni = find_executable("omniroute")
    if not omni and platform.system() == "Windows":
        omni = find_executable("omniroute.cmd")
    return omni


def get_node_bin() -> str:
    return find_executable("node")


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        try:
            s.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False


def test_gateway_response(port: int, token: str) -> tuple:
    """Tests if OmniRoute responds on port with valid authorization."""
    url = f"http://127.0.0.1:{port}/v1/models"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "AetherBridge-HealthCheck"}
    )
    try:
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("data", [])
                return True, len(models), "OK"
    except urllib.error.HTTPError as e:
        return False, 0, f"HTTP Error {e.code}"
    except Exception as e:
        return False, 0, str(e)
    return False, 0, "No response"


def get_active_config() -> tuple:
    env = sync_environments()
    port = int(env.get("OMNIROUTE_PORT", DEFAULT_PORT))
    token = env.get("OMNIROUTE_API_KEY", DEFAULT_TOKEN)
    return port, token


def check_daemon_status() -> tuple:
    system = platform.system()
    if system == "Darwin":
        installed = os.path.isfile(LAUNCHD_PLIST_PATH)
        running = False
        if installed:
            try:
                res = subprocess.run(["launchctl", "list", LAUNCHD_PLIST_ID], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                running = res.returncode == 0
            except Exception:
                pass
        return installed, running, "macOS LaunchAgent"
    elif system == "Windows":
        installed = False
        try:
            res = subprocess.run(["schtasks", "/query", "/tn", WIN_TASK_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            installed = res.returncode == 0
        except Exception:
            pass
        startup_file = os.path.join(WIN_STARTUP_DIR, "AetherBridge_OmniRoute.vbs")
        if os.path.isfile(startup_file):
            installed = True
        return installed, installed, "Windows Scheduled Task / Startup"
    elif system == "Linux":
        service_path = os.path.expanduser("~/.config/systemd/user/aetherbridge-omniroute.service")
        installed = os.path.isfile(service_path)
        running = False
        if installed:
            try:
                res = subprocess.run(["systemctl", "--user", "is-active", "aetherbridge-omniroute"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                running = "active" in res.stdout
            except Exception:
                pass
        return installed, running, "Linux systemd user service"
    return False, False, "Unknown OS"


def start_service(foreground: bool = False) -> bool:
    port, token = get_active_config()
    print(f"{CYAN}================================================================={RESET}")
    print(f"{CYAN}   🚀 AETHERBRIDGE: INICIANDO SERVICIO GATEWAY OMNIROUTE          {RESET}")
    print(f"{CYAN}================================================================={RESET}")

    # 1. Check if already running and healthy
    is_open = is_port_open(port)
    if is_open:
        ok, model_count, msg = test_gateway_response(port, token)
        if ok:
            print(f"{GREEN}✓ El Gateway ya está activo y respondiendo en el puerto {port}.{RESET}")
            print(f"  Modelos disponibles: {model_count}")
            return True
        else:
            print(f"{YELLOW}Puerto {port} ocupado pero no responde correctamente ({msg}). Intentando reiniciar...{RESET}")
            stop_service()
            time.sleep(1)

    omni_bin = get_omniroute_bin()
    if not omni_bin:
        print(f"{RED}✗ ERROR: No se encontró el binario 'omniroute' en el sistema.{RESET}")
        print("  Instálalo globalmente ejecutando: npm install -g omniroute")
        return False

    print(f"  Binario detectado: {BOLD}{omni_bin}{RESET}")
    print(f"  Puerto asignado:   {BOLD}{port}{RESET}")
    print(f"  Logs en:           {BOLD}{OUT_LOG}{RESET}")

    env = os.environ.copy()
    env["PORT"] = str(port)
    env["OMNIROUTE_PORT"] = str(port)
    env["OMNIROUTE_API_KEY"] = token
    env["REQUIRE_API_KEY"] = "true"

    # Start detached background process
    system = platform.system()
    with open(OUT_LOG, "a", encoding="utf-8") as out_f, open(ERR_LOG, "a", encoding="utf-8") as err_f:
        out_f.write(f"\n--- AetherBridge Service Boot: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        out_f.flush()

        if system == "Windows":
            # DETACHED_PROCESS = 0x00000008, CREATE_NEW_PROCESS_GROUP = 0x00000200, CREATE_NO_WINDOW = 0x08000000
            creation_flags = 0x00000008 | 0x00000200 | 0x08000000
            cmd = [omni_bin, "serve"]
            proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=out_f,
                stderr=err_f,
                creationflags=creation_flags,
                shell=True
            )
        else:
            cmd = [omni_bin, "serve"]
            proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=out_f,
                stderr=err_f,
                start_new_session=True
            )

    print(f"  Proceso lanzado (PID: {proc.pid}). Esperando inicialización...")
    for i in range(10):
        time.sleep(0.8)
        if is_port_open(port):
            ok, model_count, msg = test_gateway_response(port, token)
            if ok:
                print(f"\n{GREEN}================================================================={RESET}")
                print(f"{GREEN}   ✓ OMNIROUTE ONLINE Y VERIFICADO EXITOSAMENTE                 {RESET}")
                print(f"   Endpoint: http://127.0.0.1:{port}/v1                         ")
                print(f"   Catálogo activo: {model_count} modelos cloud listos para usar.")
                print(f"{GREEN}================================================================={RESET}\n")
                return True

    print(f"{YELLOW}Advertencia: El servicio tardó en responder. Revisa el log en: {OUT_LOG}{RESET}")
    return False


def stop_service() -> bool:
    port, token = get_active_config()
    omni_bin = get_omniroute_bin()

    print(f"{CYAN}Deteniendo servicio OmniRoute (puerto {port})...{RESET} ", end="")
    if omni_bin:
        try:
            subprocess.run([omni_bin, "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        except Exception:
            pass

    # Platform specific process cleanup if port is still occupied
    if is_port_open(port):
        system = platform.system()
        if system == "Darwin" or system == "Linux":
            try:
                subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif system == "Windows":
            try:
                subprocess.run(f'for /f "tokens=5" %a in (\'netstat -aon ^| find ":{port}" ^| find "LISTENING"\') do taskkill /f /pid %a', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    time.sleep(1)
    if not is_port_open(port):
        print(f"{GREEN}DETENIDO.{RESET}")
        return True
    else:
        print(f"{RED}No se pudo liberar el puerto {port}.{RESET}")
        return False


def install_daemon() -> bool:
    """
    Installs persistent autostart daemon:
    - macOS: ~/Library/LaunchAgents/com.aetherbridge.omniroute.plist
    - Windows: Scheduled Task / Startup VBScript
    - Linux: ~/.config/systemd/user/aetherbridge-omniroute.service
    """
    sync_environments()
    port, token = get_active_config()
    system = platform.system()
    omni_bin = get_omniroute_bin()
    node_bin = get_node_bin()

    if not omni_bin:
        print(f"{RED}✗ No se encontró 'omniroute'. Instálalo con 'npm install -g omniroute'.{RESET}")
        return False

    print(f"{CYAN}Instalando demonio de inicio automático permanente para {system}...{RESET}")

    if system == "Darwin":
        os.makedirs(os.path.dirname(LAUNCHD_PLIST_PATH), exist_ok=True)
        # Build path string
        extra_paths = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        if node_bin:
            extra_paths = f"{os.path.dirname(node_bin)}:{extra_paths}"

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCHD_PLIST_ID}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{omni_bin}</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{OUT_LOG}</string>
    <key>StandardErrorPath</key>
    <string>{ERR_LOG}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>{extra_paths}</string>
        <key>PORT</key>
        <string>{port}</string>
        <key>OMNIROUTE_PORT</key>
        <string>{port}</string>
        <key>OMNIROUTE_API_KEY</key>
        <string>{token}</string>
        <key>REQUIRE_API_KEY</key>
        <string>true</string>
    </dict>
</dict>
</plist>
"""
        with open(LAUNCHD_PLIST_PATH, "w", encoding="utf-8") as f:
            f.write(plist_content)

        # Reload with launchctl
        try:
            subprocess.run(["launchctl", "unload", LAUNCHD_PLIST_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["launchctl", "load", "-w", LAUNCHD_PLIST_PATH], check=True)
            print(f"{GREEN}✓ Demonio macOS LaunchAgent instalado y activado:{RESET}")
            print(f"  {LAUNCHD_PLIST_PATH}")
            print(f"  Inicia automáticamente al encender o desbloquear la Mac (MacBook o Mac mini).")
            return True
        except Exception as e:
            print(f"{RED}Error cargando LaunchAgent con launchctl: {e}{RESET}")
            return False

    elif system == "Windows":
        os.makedirs(WIN_STARTUP_DIR, exist_ok=True)
        vbs_path = os.path.join(WIN_STARTUP_DIR, "AetherBridge_OmniRoute.vbs")
        runner_bat = os.path.join(GLOBAL_OMNI_DIR, "start_daemon.bat")

        # Create silent bat launcher
        with open(runner_bat, "w", encoding="utf-8") as f:
            f.write(f'@echo off\n')
            f.write(f'set PORT={port}\n')
            f.write(f'set OMNIROUTE_PORT={port}\n')
            f.write(f'set OMNIROUTE_API_KEY={token}\n')
            f.write(f'set REQUIRE_API_KEY=true\n')
            f.write(f'"{omni_bin}" serve >> "{OUT_LOG}" 2>> "{ERR_LOG}"\n')

        # VBScript to run bat with zero window popup
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(f'Set WshShell = CreateObject("WScript.Shell")\n')
            f.write(f'WshShell.Run chr(34) & "{runner_bat}" & chr(34), 0\n')
            f.write(f'Set WshShell = Nothing\n')

        # Also create Scheduled Task for ONLOGON resilience
        try:
            task_cmd = f'schtasks /create /tn "{WIN_TASK_NAME}" /tr "wscript.exe \\"{vbs_path}\\"" /sc onlogon /f /rl limited'
            subprocess.run(task_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        print(f"{GREEN}✓ Servicio de inicio automático para Windows instalado exitosamente:{RESET}")
        print(f"  Acceso directo invisible en: {vbs_path}")
        print(f"  Inicia en segundo plano con Windows (Huawei, Lenovo, Dell, HP) sin abrir consolas negras.")
        return True

    elif system == "Linux":
        service_dir = os.path.expanduser("~/.config/systemd/user")
        os.makedirs(service_dir, exist_ok=True)
        service_file = os.path.join(service_dir, "aetherbridge-omniroute.service")

        unit = f"""[Unit]
Description=AetherBridge OmniRoute AI Gateway
After=network.target

[Service]
Type=simple
Environment=PORT={port}
Environment=OMNIROUTE_PORT={port}
Environment=OMNIROUTE_API_KEY={token}
Environment=REQUIRE_API_KEY=true
ExecStart={omni_bin} serve
Restart=always
RestartSec=3
StandardOutput=append:{OUT_LOG}
StandardError=append:{ERR_LOG}

[Install]
WantedBy=default.target
"""
        with open(service_file, "w", encoding="utf-8") as f:
            f.write(unit)

        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", "aetherbridge-omniroute"], check=True)
            print(f"{GREEN}✓ Servicio systemd user activado permanentemente.{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Error activando systemd: {e}{RESET}")
            return False

    return False


def uninstall_daemon() -> bool:
    system = platform.system()
    print(f"{CYAN}Desinstalando demonio de inicio automático ({system})...{RESET} ")

    if system == "Darwin":
        if os.path.isfile(LAUNCHD_PLIST_PATH):
            try:
                subprocess.run(["launchctl", "unload", LAUNCHD_PLIST_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.remove(LAUNCHD_PLIST_PATH)
                print(f"{GREEN}✓ LaunchAgent desinstalado con éxito.{RESET}")
                return True
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}")
    elif system == "Windows":
        vbs_path = os.path.join(WIN_STARTUP_DIR, "AetherBridge_OmniRoute.vbs")
        if os.path.isfile(vbs_path):
            try:
                os.remove(vbs_path)
            except Exception:
                pass
        try:
            subprocess.run(f'schtasks /delete /tn "{WIN_TASK_NAME}" /f', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        print(f"{GREEN}✓ Tarea de inicio automático en Windows desinstalada.{RESET}")
        return True
    elif system == "Linux":
        try:
            subprocess.run(["systemctl", "--user", "disable", "--now", "aetherbridge-omniroute"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            service_file = os.path.expanduser("~/.config/systemd/user/aetherbridge-omniroute.service")
            if os.path.isfile(service_file):
                os.remove(service_file)
            print(f"{GREEN}✓ Servicio systemd desinstalado.{RESET}")
            return True
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
    return False


def print_status():
    port, token = get_active_config()
    installed, daemon_running, daemon_type = check_daemon_status()
    is_open = is_port_open(port)
    http_ok, model_count, http_msg = test_gateway_response(port, token)

    print(f"{CYAN}================================================================={RESET}")
    print(f"{CYAN}   🌉 AETHERBRIDGE: ESTADO DEL SERVICIO Y ECOSISTEMA             {RESET}")
    print(f"{CYAN}   Sistema: {BOLD}{platform.system()} {platform.release()} ({platform.machine()}){RESET}")
    print(f"{CYAN}================================================================={RESET}")

    print(f"\n1. {BOLD}Gateway OmniRoute (Puerto {port}):{RESET}")
    if http_ok:
        print(f"   Estado:      {GREEN}ONLINE Y RESPONDIENDO ({model_count} modelos cloud activos){RESET}")
        print(f"   Endpoint:    http://127.0.0.1:{port}/v1")
    elif is_open:
        print(f"   Estado:      {YELLOW}PUERTO ABIERTO pero no responde ({http_msg}){RESET}")
    else:
        print(f"   Estado:      {RED}OFFLINE (Servidor apagado){RESET}")

    print(f"\n2. {BOLD}Persistencia de Inicio Automático (Daemon):{RESET}")
    print(f"   Mecanismo:   {daemon_type}")
    if installed:
        status_txt = f"{GREEN}INSTALADO Y ACTIVO{RESET}" if daemon_running else f"{YELLOW}INSTALADO{RESET}"
        print(f"   Estado:      {status_txt}")
    else:
        print(f"   Estado:      {YELLOW}NO INSTALADO (Ejecuta 'python scripts/aether_service.py install-daemon'){RESET}")

    print(f"\n3. {BOLD}Sincronización de Credenciales (api_keys.env -> ~/.omniroute/.env):{RESET}")
    has_local = os.path.isfile(LOCAL_ENV_PATH)
    has_global = os.path.isfile(GLOBAL_ENV_PATH)
    if has_local and has_global:
        print(f"   Estado:      {GREEN}SINCRONIZADO{RESET}")
    elif has_local:
        print(f"   Estado:      {YELLOW}Local presente, falta sincronizar con ~/.omniroute/.env{RESET}")
    else:
        print(f"   Estado:      {RED}Falta api_keys.env en la raíz del repositorio{RESET}")

    print(f"\n4. {BOLD}Cableado de Clientes:{RESET}")
    settings_file = os.path.expanduser("~/.claude/settings.json")
    claude_ok = False
    if os.path.isfile(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                if f":{port}" in f.read():
                    claude_ok = True
        except Exception:
            pass
    print(f"   Claude CLI:  {GREEN}CONECTADO -> localhost:{port}{RESET}" if claude_ok else f"{YELLOW}Definir ANTHROPIC_BASE_URL=http://localhost:{port}{RESET}")

    print(f"\n{CYAN}================================================================={RESET}")
    print(f"  Comandos de Control Rápido:")
    print(f"  - Iniciar Gateway:        python scripts/aether_service.py start")
    print(f"  - Detener Gateway:        python scripts/aether_service.py stop")
    print(f"  - Reiniciar y Resinc:     python scripts/aether_service.py restart")
    print(f"  - Instalar Autostart:     python scripts/aether_service.py install-daemon")
    print(f"  - Prueba Inmediata:       python scripts/aether_consult.py -m fast \"Hola\"")
    print(f"{CYAN}================================================================={RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="AetherBridge Service & Daemon Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "sync", "install-daemon", "uninstall-daemon"], default="status", nargs="?", help="Action to execute")
    parser.add_argument("--foreground", action="store_true", help="Run OmniRoute in the current foreground console")

    args = parser.parse_args()

    if args.action == "sync":
        env = sync_environments()
        print(f"{GREEN}✓ Credenciales y configuración sincronizadas correctamente en ~/.omniroute/.env ({len(env)} variables).{RESET}")
    elif args.action == "start":
        start_service(foreground=args.foreground)
    elif args.action == "stop":
        stop_service()
    elif args.action == "restart":
        stop_service()
        time.sleep(1)
        start_service()
    elif args.action == "install-daemon":
        install_daemon()
    elif args.action == "uninstall-daemon":
        uninstall_daemon()
    elif args.action == "status":
        print_status()


if __name__ == "__main__":
    main()
