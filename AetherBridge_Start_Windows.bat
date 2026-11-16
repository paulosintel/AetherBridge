@echo off
REM ==============================================================================
REM 🌉 AETHERBRIDGE: INICIADOR UNIVERSAL PARA WINDOWS (100% NATIVO)
REM Compatible con laptops Huawei, Lenovo, Dell, HP, etc. (Windows 10 / 11)
REM ==============================================================================
title AetherBridge - Servidor de IA Universal
chcp 65001 >nul

cd /d "%~dp0"

echo =================================================================
echo    🌉 AETHERBRIDGE: INICIADOR AUTOMÁTICO PARA WINDOWS
echo    Zero-Cost Frontier AI Gateway & Resilient Infrastructure
echo =================================================================
echo.

REM 1. Detectar comando de Python
set PYTHON_CMD=
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=py
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] No se encontró Python instalado en este equipo.
    echo Por favor descarga e instala Python desde: https://www.python.org/downloads/
    echo Asegúrate de marcar la casilla "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

REM 2. Sincronizar credenciales y levantar servicio en segundo plano
echo [1/3] Sincronizando credenciales (api_keys.env -> .omniroute)...
%PYTHON_CMD% scripts\aether_service.py sync
echo.

echo [2/3] Levantando Gateway OmniRoute en segundo plano (puerto 20128)...
%PYTHON_CMD% scripts\aether_service.py start
echo.

REM 3. Preguntar si desea registrar inicio automático con Windows
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AetherBridge_OmniRoute.vbs" (
    echo [Opcional] ¿Deseas que AetherBridge inicie automáticamente cada vez que enciendas la PC?
    set /p AUTOSTART="Instalar demonio en segundo plano (S/N)? [S]: "
    if /i not "%AUTOSTART%"=="n" (
        %PYTHON_CMD% scripts\aether_service.py install-daemon
    )
    echo.
)

REM 4. Diagnóstico de Salud
echo [3/3] Verificando salud del ecosistema...
%PYTHON_CMD% scripts\verify_setup.py

echo.
echo =================================================================
echo ¿Qué deseas hacer ahora?
echo 1) Abrir Claude CLI (Claude Code) conectado a AetherBridge
echo 2) Probar consulta rápida (LPU Ultra-Rápido)
echo 3) Salir (El servidor seguirá corriendo en segundo plano)
echo =================================================================
set /p OPT="Selecciona una opción [1]: "

if "%OPT%"=="2" (
    echo.
    %PYTHON_CMD% scripts\aether_consult.py -m fast "¿Hola, estás listo para programar?"
    echo.
    pause
    goto end
)

if "%OPT%"=="" set OPT=1
if "%OPT%"=="1" (
    where claude >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo Iniciando Claude CLI...
        claude
    ) else (
        echo.
        echo [Aviso] Claude CLI no está instalado globalmente.
        echo Puedes instalarlo con: npm install -g @anthropic-ai/claude-code
        echo O usar el gateway con Codex, Antigravity o tus scripts.
        echo.
        pause
    )
)

:end
