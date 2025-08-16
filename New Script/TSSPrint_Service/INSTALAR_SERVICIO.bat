@echo off
:: INSTALAR_SERVICIO_CORRECTO.BAT

:: Cambiar página de códigos a UTF-8
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

:: Ejecutar el script de PowerShell y esperar a que termine
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_service.ps1"

:: Pausar al final para ver errores
echo.
echo Presione cualquier tecla para cerrar...
pause >nul
