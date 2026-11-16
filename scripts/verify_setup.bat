@echo off
REM ==============================================================================
REM AetherBridge: Lanzador de Diagnostico Universal para Windows CMD / Doble Clic
REM ==============================================================================
title AetherBridge - Diagnostico de Infraestructura

REM Mover al directorio raíz del repositorio AetherBridge
cd /d "%~dp0.."

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python scripts\verify_setup.py
    goto end
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py scripts\verify_setup.py
    goto end
)

powershell -ExecutionPolicy Bypass -File "%~dp0verify_setup.ps1"

:end
echo.
pause
