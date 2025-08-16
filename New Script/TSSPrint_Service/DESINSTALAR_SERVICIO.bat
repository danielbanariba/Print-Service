@echo off
:: DESINSTALAR_SERVICIO.BAT

:: Cambiar página de códigos a UTF-8 para caracteres especiales
chcp 65001 >nul 2>&1

:: Verificar permisos de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ════════════════════════════════════════════════════════
    echo    Solicitando permisos de Administrador...
    echo ════════════════════════════════════════════════════════
    echo.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

:: Ejecutar el script de PowerShell
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0uninstall_service.ps1"

exit
