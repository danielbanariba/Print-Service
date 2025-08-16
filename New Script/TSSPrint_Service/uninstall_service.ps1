# uninstall_service.ps1
# Desinstalador del servicio TSSPrintService

$ServiceName = "TSSPrintService"

try {
    # Comprobar si el servicio existe
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($null -eq $svc) {
        Write-Host "El servicio '$ServiceName' NO está instalado." -ForegroundColor Yellow
        Pause
        exit
    }

    # Detener el servicio si está corriendo
    if ($svc.Status -eq 'Running') {
        Write-Host "Deteniendo el servicio '$ServiceName'..."
        Stop-Service -Name $ServiceName -Force -ErrorAction Stop
        Start-Sleep -Seconds 2
    }

    # Eliminar el servicio
    Write-Host "Eliminando el servicio '$ServiceName'..."
    sc.exe delete $ServiceName | Out-Null

    Write-Host "Servicio '$ServiceName' desinstalado correctamente." -ForegroundColor Green
    Pause
}
catch {
    Write-Host "Ocurrió un error: $_" -ForegroundColor Red
    Pause
}
