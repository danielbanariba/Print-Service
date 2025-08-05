@echo off
echo Instalando TSS Print Service...
cd /d "%~dp0"
TSSPrint.exe install
echo.
echo Servicio instalado correctamente.
echo Para iniciar el servicio use: TSSPrint.exe start
pause