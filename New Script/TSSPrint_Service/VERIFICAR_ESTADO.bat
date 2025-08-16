@echo off
:: VERIFICAR_ESTADO.bat
:: Verificador del Estado del Servicio TSSPrint
:: Version: 1.3

:: Habilitar delayed expansion
setlocal enabledelayedexpansion

:: Cambiar página de códigos a UTF-8
chcp 65001 >nul 2>&1

cls
echo ╔════════════════════════════════════════════════╗
echo ║     ESTADO DEL SERVICIO TSSPRINT              ║
echo ╚════════════════════════════════════════════════╝
echo.

:: Verificar si el servicio existe
sc query TSSPrintService >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ El servicio NO está instalado
    echo.
    echo Para instalar, ejecute: INSTALAR_SERVICIO.bat
) else (
    echo ✓ Servicio instalado
    echo.

    :: Capturar el estado correctamente (columna 4)
    for /f "tokens=4" %%A in ('sc query TSSPrintService ^| findstr "STATE"') do (
        set estado=%%A
    )

    if /I "!estado!"=="RUNNING" (
        echo ✓ El servicio está LEVANTADO y CORRIENDO.
    ) else if /I "!estado!"=="STOPPED" (
        echo ✗ El servicio está DETENIDO.
    ) else (
        echo ! El servicio está en estado: !estado!
    )

    echo.
)
echo.
echo Presione cualquier tecla para cerrar...
pause >nul
