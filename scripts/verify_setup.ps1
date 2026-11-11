# ==============================================================================
# AETHERBRIDGE: SCRIPT DE DIAGNÓSTICO PARA WINDOWS POWERSHELL
# Proveedor Directo OmniRoute Gateway + Claude CLI / Codex (Ollama Opcional)
# ==============================================================================

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   🌉 AETHERBRIDGE: DIAGNÓSTICO EN WINDOWS (POWERSHELL)           " -ForegroundColor Cyan
Write-Host "   Proveedores Directos Cloud vía OmniRoute - AetherBridge       " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar OmniRoute Gateway
$port = if ($env:OMNIROUTE_PORT) { $env:OMNIROUTE_PORT } else { "20128" }
Write-Host "[1/5] Verificando Gateway OmniRoute en puerto $port... " -NoNewline
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
    Write-Host "      Tip: Inicia el motor con 'omniroute serve'."
}

# 2. Verificar api_keys.env
Write-Host "`n[2/5] Verificando credenciales 'api_keys.env'... " -NoNewline
if (Test-Path "api_keys.env") {
    $count = (Get-Content "api_keys.env" | Where-Object { $_ -match '=' -and $_ -notmatch '^\s*#' }).Count
    Write-Host "ENCONTRADO ($count variables detectadas)" -ForegroundColor Green
} elseif (Test-Path "api_keys.env.example") {
    Write-Host "SOLO PLANTILLA DETECTADA (api_keys.env.example)" -ForegroundColor Yellow
} else {
    Write-Host "NO ENCONTRADO." -ForegroundColor Red
}

# 3. Verificar Claude CLI
Write-Host "`n[3/5] Verificando cableado de Claude CLI... " -NoNewline
$settingsPath = Join-Path $env:USERPROFILE ".claude\settings.json"
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

# 4. Verificar Ollama (Opcional)
Write-Host "`n[4/5] Verificando nodo local Ollama (Opcional)... " -NoNewline
try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "ACTIVO (localhost:11434)" -ForegroundColor Green
} catch {
    Write-Host "OPCIONAL - No instalado/inactivo (operando vía OmniRoute Cloud)" -ForegroundColor Cyan
}

# 5. Suite de Scripts
Write-Host "`n[5/5] Verificando suite de scripts AetherBridge en scripts\... " -NoNewline
$req = @("gemini_sandwich.py", "aether_consult.py", "auto_update_catalog.py", "omniroute_mcp_bridge.js")
$allExist = ($req | Where-Object { -not (Test-Path "scripts\$_") }).Count -eq 0
if ($allExist) {
    Write-Host "SUITE COMPLETA (Sandwich, Consult, MCP Bridge, AutoUpdate)" -ForegroundColor Green
} else {
    Write-Host "Faltan scripts en la carpeta scripts\" -ForegroundColor Yellow
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  Diagnóstico finalizado. Para consultas rápidas:                " -ForegroundColor Green
Write-Host "  python scripts\aether_consult.py -m sonnet `"¿Hola Mundo?`""
Write-Host "=================================================================" -ForegroundColor Cyan
