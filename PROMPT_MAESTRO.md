# 🧙‍♂️ AetherBridge: Prompt Maestro de Autodespliegue

> **Copia y pega este prompt directamente en cualquier agente de desarrollo con acceso a terminal y sistema**  
> (por ejemplo: **Antigravity**, **Codex CLI**, o **Claude Code**).  
> El agente configurará toda la infraestructura de forma autónoma y persistente.

---

```text
Actúa como mi Ingeniero Senior de Infraestructura y DevOps de IA para el proyecto AetherBridge.
Tu objetivo es configurar un ecosistema unificado y ultra-resiliente de más de 300 modelos locales y en la nube a costo $0, de manera que pueda consumirlo fluidamente desde Claude CLI (Claude Code), Codex y scripts locales sin pagar suscripciones recurrentes.

Sigue rigurosamente estos pasos sin pedirme intervención manual, salvo que falte una credencial crítica:

1. COMPROBACIÓN E INSTALACIÓN DE DEPENDENCIAS BASE (Detecta el Sistema Operativo):
   a) Verifica si Node.js y el motor gateway OmniRoute están disponibles:
      - Si falta Node.js en Windows: `winget install OpenJS.NodeJS`. En macOS: `brew install node`.
      - Si falta OmniRoute (en cualquier SO): Ejecuta `npm install -g omniroute`.
   b) Verifica si Ollama está instalado (nodo local opcional para offline):
      - En Windows: `winget install Ollama.Ollama` (o guía a https://ollama.com/download/windows).
      - En macOS: `brew install ollama`.
      - En Linux: `curl -fsSL https://ollama.com/install.sh | sh`.
   c) Si Ollama está instalado, asegura que esté activo y descarga un modelo ligero:
      - `ollama pull llama3.2` o `ollama pull qwen2.5-coder:3b`.

2. CONFIGURACIÓN Y SINCRONIZACIÓN DE CREDENCIALES:
   a) Revisa 'api_keys.env' en la raíz (si no existe, crea una copia a partir de 'api_keys.env.example').
   b) Sincroniza las credenciales y el puerto con el motor OmniRoute ejecutando:
      - En Windows: `python scripts\aether_service.py sync` (o `py scripts\aether_service.py sync`).
      - En macOS/Linux: `python3 scripts/aether_service.py sync`.
      (Esto vincula automáticamente tus claves de Google Gemini, Groq, Cerebras, SambaNova, OpenRouter, NVIDIA, etc. con el archivo de configuración global del usuario).

3. LEVANTAMIENTO Y PERSISTENCIA AUTOMÁTICA DEL GATEWAY (PUERTO 20128):
   a) Configura e instala el demonio persistente en segundo plano:
      - En Windows: `python scripts\aether_service.py install-daemon` (crea un inicio invisible que sobrevive reinicios y suspensión en laptops Huawei/PC).
      - En macOS: `python3 scripts/aether_service.py install-daemon` (instala un LaunchAgent permanente para que no muera al cerrar la tapa de tu MacBook ni al reiniciar).
      - En Linux: `python3 scripts/aether_service.py install-daemon` (habilita servicio systemd user).
   b) Inicia el servicio en segundo plano:
      - `python scripts/aether_service.py start` (o `python3 scripts/aether_service.py start`).
   c) Realiza una petición de validación a http://localhost:20128/v1/models para confirmar que está online y respondiendo.

4. CABLEADO DE CLIENTES DE DESARROLLO (CROSS-PLATFORM):
   a) Para Claude CLI (Claude Code):
      - Asegura que ~/.claude/settings.json (o %USERPROFILE%\.claude\settings.json) tenga:
        {"env": {"ANTHROPIC_BASE_URL": "http://localhost:20128", "ANTHROPIC_AUTH_TOKEN": "omniroute-secret-key-local"}}
   b) Para Codex (Escritorio / CLI):
      - Configura el endpoint OpenAI-compatible apuntando a:
        Base URL: http://localhost:20128/v1
        API Key: omniroute-secret-key-local
   c) Permisos y Diagnóstico de Salud Universal:
      - En macOS/Linux: `chmod +x scripts/*.sh scripts/*.py scripts/*.js AetherBridge_Start_Mac.command`
      - Ejecuta el diagnóstico universal de salud:
        `python scripts/verify_setup.py` (o `python3 scripts/verify_setup.py`).

5. REPORTE FINAL DE AUDITORÍA:
   Entrega un informe visual en tabla que incluya:
   - Sistema Operativo detectado (Windows Huawei/PC / macOS MacBook/Mac mini / Linux).
   - Estado de OmniRoute Gateway (puerto 20128 y catálogo de modelos cloud activos).
   - Estado de Persistencia (Daemon LaunchAgent / Windows Startup activo).
   - Estado de Ollama (modelos instalados o modo Cloud Directo).
   - Demostración de prueba ejecutando `python scripts/aether_consult.py -m fast "Hola"`.
```

---

## ⚡ Variación Rápida (Solo Arranque y Verificación)

Si ya descargaste el repositorio y tienes las herramientas instaladas, usa este prompt conciso:

```text
Ejecuta 'python scripts/aether_service.py sync', levanta el gateway persistente con 'python scripts/aether_service.py install-daemon' y 'python scripts/aether_service.py start', y corre 'python scripts/verify_setup.py' confirmando que todo el circuito esté en verde.
```
