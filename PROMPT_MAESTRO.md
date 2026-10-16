# 🧙‍♂️ AetherBridge: Prompt Maestro de Autodespliegue

> **Copia y pega este prompt directamente en cualquier agente de desarrollo con acceso a terminal y sistema**  
> (por ejemplo: **Antigravity**, **Codex CLI**, o **Claude Code**).  
> El agente configurará toda la infraestructura de forma autónoma.

---

```text
Actúa como mi Ingeniero Senior de Infraestructura y DevOps de IA para el proyecto AetherBridge.
Tu objetivo es configurar un ecosistema unificado y resiliente de más de 300 modelos locales y en la nube a costo $0, de manera que pueda consumirlo desde Claude CLI (Claude Code), Codex y scripts locales sin pagar suscripciones recurrentes.

Sigue rigurosamente estos pasos sin pedirme intervención manual, salvo que falte una credencial crítica:

1. COMPROBACIÓN E INSTALACIÓN DE DEPENDENCIAS BASE (Detecta el Sistema Operativo):
   a) Verifica si Ollama está instalado. Si no está instalado:
      - En Windows: Ejecuta `winget install Ollama.Ollama` (o guía a descargar de https://ollama.com/download/windows).
      - En macOS: Ejecuta `brew install ollama`.
      - En Linux: Ejecuta `curl -fsSL https://ollama.com/install.sh | sh`.
   b) Verifica si Node.js y el motor gateway OmniRoute están disponibles:
      - Si falta Node.js en Windows: `winget install OpenJS.NodeJS`. En macOS: `brew install node`.
      - Si falta OmniRoute (en cualquier SO): Ejecuta `npm install -g omniroute`.
   c) Asegúrate de que el servicio de Ollama esté activo en segundo plano (puerto 11434).
   d) Descarga un modelo liviano y eficiente para codificación y uso offline:
      - Ejecuta: `ollama pull llama3.2` o `ollama pull qwen2.5-coder:3b`.

2. CONFIGURACIÓN DE PROVEEDORES Y CREDENCIALES:
   a) Revisa el archivo 'api_keys.env' en la raíz del proyecto (si no existe, crea una copia a partir de 'api_keys.env.example').
   b) Configura el motor para registrar los proveedores que cuenten con claves válidas (Google Gemini, Groq, Cerebras, SambaNova, OpenRouter, Mistral, Together AI, etc.).
   c) Conecta Ollama como proveedor local primario de respaldo offline (localhost:11434).
   d) Configura la estrategia de enrutamiento resiliente:
      - Prioridad 1: Proveedores ultra-rápidos con tiers gratuitos (Groq LPU, Cerebras, Google Gemini).
      - Prioridad 2: Respaldo automático por cuota/rate-limit hacia SambaNova, OpenRouter o DeepInfra.
      - Prioridad 3: Respaldo final a Ollama local si falla el internet o se agotan cuotas externas.

3. LEVANTAMIENTO Y VALIDACIÓN DEL GATEWAY:
   a) Inicia el servicio en segundo plano en el puerto 20128:
      `omniroute serve` (o el comando de background correspondiente según el sistema operativo).
   b) Realiza una petición de validación a http://localhost:20128/v1/models para confirmar que está online y respondiendo.

4. CABLEADO DE CLIENTES DE DESARROLLO (CROSS-PLATFORM):
   a) Para Claude CLI (Claude Code):
      - En Windows (PowerShell):
        `[System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', 'http://localhost:20128', 'User')`
        `[System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'sk-aetherbridge', 'User')`
        o escribe en `$env:USERPROFILE\.claude\settings.json`:
        `{"env": {"ANTHROPIC_BASE_URL": "http://localhost:20128", "ANTHROPIC_AUTH_TOKEN": "sk-aetherbridge"}}`
      - En macOS / Linux:
        Configura en ~/.zshrc o ~/.bashrc o ~/.claude/settings.json:
        ANTHROPIC_BASE_URL="http://localhost:20128"
        ANTHROPIC_AUTH_TOKEN="sk-aetherbridge"
   b) Para Codex (Escritorio / CLI):
      - Configura el endpoint OpenAI-compatible apuntando a:
        Base URL: http://localhost:20128/v1
        API Key: sk-aetherbridge
   c) Permisos y Diagnóstico de Salud:
      - En macOS/Linux: `chmod +x scripts/*.sh scripts/*.py scripts/*.js`
      - En Windows: No requiere chmod.
      - Ejecuta el diagnóstico universal de salud:
        `python scripts/verify_setup.py` (o `./scripts/verify_setup.sh` en Bash, o `.\scripts\verify_setup.ps1` en PowerShell).

5. REPORTE FINAL DE AUDITORÍA:
   Entrega un informe visual en tabla que incluya:
   - Sistema Operativo detectado (Windows / macOS / Linux).
   - Estado de Ollama (modelos instalados y listos para offline).
   - Estado del Gateway (puerto 20128 y lista de proveedores activos).
   - Comando exacto para abrir Claude CLI listo con el puente en este sistema.
   - Demostración de prueba ejecutando `python scripts/aether_consult.py -m fast "Hola"`.
```

---

## ⚡ Variación Rápida (Solo Arranque y Verificación)

Si ya descargaste el repositorio y tienes las herramientas instaladas, usa este prompt conciso:

```text
Lee 'api_keys.env', levanta Ollama y el gateway en segundo plano (puerto 20128), asegura que ANTHROPIC_BASE_URL apunte a http://localhost:20128 con token 'sk-aetherbridge', y ejecuta 'python scripts/verify_setup.py' confirmando que todo el circuito esté en verde.
```
