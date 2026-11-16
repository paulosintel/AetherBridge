# ==============================================================================
# AETHERBRIDGE: SCRIPT DE DIAGNÓSTICO PARA WINDOWS POWERSHELL
# Proveedor Directo OmniRoute Gateway + Claude CLI / Codex (Ollama Opcional)
# ==============================================================================

# Asegurar que el directorio de trabajo sea la raíz del repositorio
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $ScriptDir "..")

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   🌉 AETHERBRIDGE: DIAGNÓSTICO EN WINDOWS (POWERSHELL)           " -ForegroundColor Cyan
Write-Host "   Proveedores Directos Cloud vía OmniRoute - AetherBridge       " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar OmniRoute Gateway
$port = if ($env:OMNIROUTE_PORT) { $env:OMNIROUTE_PORT } else { "20128" }
Write-Host "[1/6] Verificando Gateway OmniRoute en puerto $port... " -NoNewline
try {
    $token = if ($env:OMNIROUTE_API_KEY) { $env:OMNIROUTE_API_KEY } else { "omniroute-secret-key-local" }
    $headers = @{ "Authorization" = "Bearer $token" }
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v1/models" -Headers $headers -TimeoutSec 4 -ErrorAction Stop
    Write-Host "ONLINE y RESPONDIENDO (localhost:$port)" -ForegroundColor Green
    if ($resp.data) {
        Write-Host "      Catálogo activo: $($resp.data.Count) modelos disponibles vía AetherBridge."
    }
} catch {
    Write-Host "OFFLINE o NO RESPONDE." -ForegroundColor Yellow
    Write-Host "      Tip: Inicia el servicio con 'python scripts\aether_service.py start'."
}

# 2. Verificar api_keys.env y sincronización
Write-Host "`n[2/6] Verificando credenciales 'api_keys.env' y sincronización... " -NoNewline
$globalEnv = Join-Path $env:USERPROFILE ".omniroute\.env"
if (Test-Path "api_keys.env") {
    $count = (Get-Content "api_keys.env" | Where-Object { $_ -match '=' -and $_ -notmatch '^\s*#' }).Count
    if (Test-Path $globalEnv) {
        Write-Host "SINCRONIZADO ($count variables detectadas)" -ForegroundColor Green
    } else {
        Write-Host "LOCAL ACTIVO ($count claves), falta sincronizar con .omniroute" -ForegroundColor Yellow
        Write-Host "      Tip: Ejecuta 'python scripts\aether_service.py sync'"
    }
} elseif (Test-Path "api_keys.env.example") {
    Write-Host "SOLO PLANTILLA DETECTADA (api_keys.env.example)" -ForegroundColor Yellow
} else {
    Write-Host "NO ENCONTRADO." -ForegroundColor Red
}

# 3. Verificar persistencia de inicio automático
Write-Host "`n[3/6] Verificando persistencia de servicio (Daemon Windows)... " -NoNewline
$startupVbs = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\AetherBridge_OmniRoute.vbs"
if (Test-Path $startupVbs) {
    Write-Host "CONFIGURADO (Inicio invisible al iniciar sesión en Windows)" -ForegroundColor Green
} else {
    Write-Host "NO CONFIGURADO (Solo manual)" -ForegroundColor Yellow
    Write-Host "      Tip: Ejecuta 'python scripts\aether_service.py install-daemon'"
}

# 4. Verificar Claude CLI y Desktop
Write-Host "`n[4/6] Verificando cableado de Claude CLI y Desktop... " -NoNewline
$settingsPath = Join-Path $env:USERPROFILE ".claude\settings.json"
$desktopPath = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
$configured = $false
if (Test-Path $settingsPath) {
    if ((Get-Content $settingsPath -Raw) -match "ANTHROPIC_BASE_URL") {
        Write-Host "CONFIGURADO en $settingsPath" -ForegroundColor Green
        $configured = $true
    }
}
if (-not $configured) {
    if ($env:ANTHROPIC_BASE_URL) {
        Write-Host "ACTIVO vía variable de entorno: $env:ANTHROPIC_BASE_URL" -ForegroundColor Green
    } else {
        Write-Host "SIN CONFIGURAR." -ForegroundColor Yellow
    }
}

# 5. Verificar Ollama (Opcional)
Write-Host "`n[5/6] Verificando nodo local Ollama (Opcional)... " -NoNewline
try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "ACTIVO (localhost:11434)" -ForegroundColor Green
} catch {
    Write-Host "OPCIONAL - No instalado/inactivo (operando vía OmniRoute Cloud)" -ForegroundColor Cyan
}

# 6. Suite de Scripts
Write-Host "`n[6/6] Verificando suite de scripts AetherBridge en scripts\... " -NoNewline
$req = @("aether_service.py", "gemini_sandwich.py", "aether_consult.py", "auto_update_catalog.py", "omniroute_mcp_bridge.js")
$allExist = ($req | Where-Object { -not (Test-Path "scripts\$_") }).Count -eq 0
if ($allExist) {
    Write-Host "SUITE COMPLETA (Service Daemon, Sandwich, Consult, MCP Bridge, AutoUpdate)" -ForegroundColor Green
} else {
    Write-Host "Faltan scripts en la carpeta scripts\" -ForegroundColor Yellow
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  Diagnóstico finalizado. Comandos útiles en Windows:             " -ForegroundColor Green
Write-Host "  - Iniciar Gateway:    python scripts\aether_service.py start"
Write-Host "  - Instalar Daemon:    python scripts\aether_service.py install-daemon"
Write-Host "  - Consulta rápida:    python scripts\aether_consult.py -m fast `"Hola`""
Write-Host "=================================================================" -ForegroundColor Cyan
