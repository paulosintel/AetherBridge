# ==============================================================================
# AETHERBRIDGE: SCRIPT DE DIAGNÓSTICO PARA WINDOWS POWERSHELL
# Ollama + OmniRoute Gateway + Claude CLI / Codex
# ==============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   🌉 AETHERBRIDGE: DIAGNÓSTICO EN WINDOWS (POWERSHELL)           " -ForegroundColor Cyan
Write-Host "   Democratización de Modelos Cloud Gratuitos & Nodos Locales    " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Ollama
Write-Host "[1/5] Verificando servicio de Ollama (Resiliencia Local)... " -NoNewline
try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "ACTIVO (localhost:11434)" -ForegroundColor Green
    if ($resp.models) {
        Write-Host "      Modelos locales listos en Ollama:"
        foreach ($m in $resp.models) {
            Write-Host "      - $($m.name)"
        }
    }
} catch {
    $ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollamaCmd) {
        Write-Host "INSTALADO pero NO ACTIVO." -ForegroundColor Yellow
        Write-Host "      Tip: Abre la aplicación Ollama desde el Menú Inicio o ejecuta 'ollama serve'."
    } else {
        Write-Host "NO INSTALADO." -ForegroundColor Red
        Write-Host "      Tip Windows: Ejecuta 'winget install Ollama.Ollama' o descárgalo de https://ollama.com/download/windows"
    }
}

# 2. Verificar api_keys.env
Write-Host "`n[2/5] Verificando credenciales 'api_keys.env'... " -NoNewline
if (Test-Path "api_keys.env") {
    $count = (Get-Content "api_keys.env" | Where-Object { $_ -match '=' -and $_ -notmatch '^\s*#' }).Count
    Write-Host "ENCONTRADO ($count variables detectadas)" -ForegroundColor Green
} elseif (Test-Path "api_keys.env.example") {
    Write-Host "SOLO PLANTILLA DETECTADA (api_keys.env.example)" -ForegroundColor Yellow
    Write-Host "      Tip: Copia 'api_keys.env.example' como 'api_keys.env' y añade al menos 1 clave gratuita."
} else {
    Write-Host "NO ENCONTRADO." -ForegroundColor Red
}

# 3. Verificar OmniRoute Gateway
$port = if ($env:OMNIROUTE_PORT) { $env:OMNIROUTE_PORT } else { "20128" }
Write-Host "`n[3/5] Verificando Gateway OmniRoute en puerto $port... " -NoNewline
try {
    $token = if ($env:OMNIROUTE_API_KEY) { $env:OMNIROUTE_API_KEY } else { "sk-aetherbridge" }
    $headers = @{ "Authorization" = "Bearer $token" }
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$port/v1/models" -Headers $headers -TimeoutSec 4 -ErrorAction Stop
    Write-Host "ONLINE y RESPONDIENDO (localhost:$port)" -ForegroundColor Green
    if ($resp.data) {
        Write-Host "      Catálogo activo: $($resp.data.Count) modelos disponibles vía AetherBridge."
    }
} catch {
    Write-Host "OFFLINE o NO RESPONDE." -ForegroundColor Yellow
    Write-Host "      Tip: Inicia el motor con 'omniroute serve' o mediante el Prompt Maestro."
}

# 4. Verificar Claude CLI
Write-Host "`n[4/5] Verificando cableado de Claude CLI... " -NoNewline
$settingsPath = Join-Path $env:USERPROFILE ".claude\settings.json"
$configured = $false

if (Test-Path $settingsPath) {
    $content = Get-Content $settingsPath -Raw
    if ($content -match "ANTHROPIC_BASE_URL") {
        Write-Host "CONFIGURADO en $settingsPath" -ForegroundColor Green
        $configured = $true
    }
}

if (-not $configured) {
    if ($env:ANTHROPIC_BASE_URL) {
        Write-Host "ACTIVO vía variable de entorno: $env:ANTHROPIC_BASE_URL" -ForegroundColor Green
    } else {
        Write-Host "SIN CONFIGURAR." -ForegroundColor Yellow
        Write-Host "      Tip Windows (PowerShell):"
        Write-Host "        [System.Environment]::SetEnvironmentVariable('ANTHROPIC_BASE_URL', 'http://localhost:20128', 'User')"
        Write-Host "        [System.Environment]::SetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN', 'sk-aetherbridge', 'User')"
    }
}

# 5. Suite de Scripts
Write-Host "`n[5/5] Verificando suite de scripts AetherBridge en scripts\... " -NoNewline
$req = @("gemini_sandwich.py", "aether_consult.py", "auto_update_catalog.py", "omniroute_mcp_bridge.js")
$allExist = $true
foreach ($f in $req) {
    if (-not (Test-Path "scripts\$f")) { $allExist = $false }
}
if ($allExist) {
    Write-Host "SUITE COMPLETA (Sandwich, Consult, MCP Bridge, AutoUpdate)" -ForegroundColor Green
} else {
    Write-Host "Faltan scripts en la carpeta scripts\" -ForegroundColor Yellow
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  Diagnóstico finalizado. Para consultas rápidas:                " -ForegroundColor Green
Write-Host "  python scripts\aether_consult.py -m fast `"¿Hola Mundo?`""
Write-Host "=================================================================" -ForegroundColor Cyan
