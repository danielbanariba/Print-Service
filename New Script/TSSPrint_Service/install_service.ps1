# install_service.ps1

# AUTO-ELEVACION A ADMINISTRADOR
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    # Reejecutar el script como administrador
    $arguments = "& '" + $myinvocation.mycommand.definition + "'"
    Start-Process powershell -Verb runAs -ArgumentList $arguments -WindowStyle Normal
    exit
}

# CONFIGURACION DE POLITICA DE EJECUCION TEMPORAL
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Configuracion
$serviceName = "TSSPrintService"
$serviceDisplayName = "TSSPrint_CRM2_V2"
$servicePath = "C:\Print-Service"
$exeName = "TSSPrint.exe"

# Detectar ubicacion del script actual
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$sourceExe = Join-Path $scriptPath $exeName
$targetExe = Join-Path $servicePath $exeName

# Cambiar al directorio del script
Set-Location $scriptPath

# Funcion para mostrar mensajes con color
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Funcion para pausar antes de cerrar
function Pause-Exit {
    param($seconds = 5)
    Write-Host ""
    Write-Host "La ventana se cerrara en $seconds segundos..." -ForegroundColor Gray
    Start-Sleep -Seconds $seconds
}

Clear-Host
Write-Host ""
Write-ColorOutput Yellow "INSTALADOR DEL SERVICIO TSSPRINT"
Write-Host ""

# Verificar que existe el archivo exe
if (!(Test-Path $sourceExe)) {
    Write-ColorOutput Red "[ERROR] No se encontro el archivo $exeName"
    Write-Host "Ubicacion esperada: $sourceExe"
    Write-Host ""
    Write-Host "Asegurese de que $exeName este en la misma carpeta que este script"
    Pause-Exit 10
    exit 1
}

try {
    Write-Host "[1/6] Verificando estado del servicio anterior..." -ForegroundColor Cyan

    # Detener servicio si existe
    $existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "  - Servicio existente detectado. Actualizando..." -ForegroundColor Yellow
        
        if ($existingService.Status -eq 'Running') {
            Write-Host "  - Deteniendo servicio actual..." -ForegroundColor Yellow
            Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Desinstalar servicio anterior
        Write-Host "  - Desinstalando version anterior..." -ForegroundColor Yellow
        & $targetExe remove 2>&1 | Out-Null
        Start-Sleep -Seconds 2
    }

    Write-Host "[2/6] Creando estructura de carpetas..." -ForegroundColor Cyan

    # Crear carpeta si no existe
    if (!(Test-Path $servicePath)) {
        New-Item -ItemType Directory -Path $servicePath -Force | Out-Null
        Write-Host "  - Carpeta creada: $servicePath" -ForegroundColor Green
    } else {
        Write-Host "  - Carpeta existente: $servicePath" -ForegroundColor Green
    }

    Write-Host "[3/6] Copiando archivos del servicio..." -ForegroundColor Cyan

    # Terminar proceso si esta en uso
    $processUsingFile = Get-Process | Where-Object { $_.Path -eq $targetExe } -ErrorAction SilentlyContinue
    if ($processUsingFile) {
        Write-Host "  - Terminando proceso en ejecucion..." -ForegroundColor Yellow
        $processUsingFile | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    # Copiar exe al destino
    Copy-Item -Path $sourceExe -Destination $targetExe -Force -ErrorAction Stop
    Write-Host "  - Archivo copiado exitosamente" -ForegroundColor Green

    Write-Host "[4/6] Registrando el servicio en Windows..." -ForegroundColor Cyan

    # Registrar servicio
    $installOutput = & $targetExe install 2>&1
    if ($LASTEXITCODE -eq 0 -or $installOutput -like "*already exists*") {
        Write-Host "  - Servicio registrado correctamente" -ForegroundColor Green
    } else {
        Write-Host "  - Error al registrar servicio: $installOutput" -ForegroundColor Red
        throw "Error al registrar servicio: $installOutput"
    }

    Write-Host "[5/6] Configurando propiedades del servicio..." -ForegroundColor Cyan

    # Configurar el servicio
    Set-Service -Name $serviceName -StartupType Automatic -ErrorAction SilentlyContinue
    Write-Host "  - Servicio configurado para inicio automatico" -ForegroundColor Green
    
    # Configurar recuperacion ante fallos
    & sc.exe failure $serviceName reset= 86400 actions= restart/60000/restart/60000// 2>&1 | Out-Null
    Write-Host "  - Recuperacion automatica configurada" -ForegroundColor Green

    Write-Host "[6/6] Iniciando el servicio..." -ForegroundColor Cyan

    # Iniciar servicio
    try {
        Start-Service -Name $serviceName -ErrorAction Stop
        Start-Sleep -Seconds 2
        
        # Verificar estado
        $service = Get-Service -Name $serviceName
        if ($service.Status -eq 'Running') {
            Write-Host "  - Servicio iniciado correctamente" -ForegroundColor Green
        } else {
            Write-Host "  - Intentando iniciar manualmente..." -ForegroundColor Yellow
            & $targetExe start 2>&1 | Out-Null
            Start-Sleep -Seconds 3
            $service = Get-Service -Name $serviceName
            if ($service.Status -eq 'Running') {
                Write-Host "  - Servicio iniciado correctamente" -ForegroundColor Green
            } else {
                Write-Host "  - Advertencia: El servicio no se pudo iniciar automaticamente" -ForegroundColor Yellow
                Write-Host "    Puede intentar iniciarlo manualmente con: sc start $serviceName" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "  - Error al iniciar servicio: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "    Puede intentar iniciarlo manualmente con: sc start $serviceName" -ForegroundColor Gray
    }

    # Verificar puertos (sin errores si fallan)
    Write-Host ""
    Write-Host "Verificando puertos de escucha..." -ForegroundColor Cyan
    $port9000 = Test-NetConnection -ComputerName localhost -Port 9000 -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null
    $port9001 = Test-NetConnection -ComputerName localhost -Port 9001 -InformationLevel Quiet -WarningAction SilentlyContinue 2>$null

    if ($port9000 -or $port9001) {
        Write-Host "  - Puerto 9000: $(if($port9000){'+ Activo'}else{'- Inactivo'})" -ForegroundColor $(if($port9000){'Green'}else{'Yellow'})
        Write-Host "  - Puerto 9001: $(if($port9001){'+ Activo'}else{'- Inactivo'})" -ForegroundColor $(if($port9001){'Green'}else{'Yellow'})
    } else {
        Write-Host "  - Los puertos estan activandose..." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-ColorOutput Green "INSTALACION COMPLETADA"
    Write-Host ""
    Write-Host "Servicio: $serviceDisplayName" -ForegroundColor White
    Write-Host "Estado: " -NoNewline
    Write-ColorOutput Green "Activo y funcionando"
    Write-Host "Ubicacion: $targetExe" -ForegroundColor White
    Write-Host "Puertos: localhost:9000, localhost:9001" -ForegroundColor White
    Write-Host ""
    
    # Cerrar automaticamente despues de 5 segundos
    Pause-Exit 5

} catch {
    Write-Host ""
    Write-ColorOutput Red "ERROR EN INSTALACION"
    Write-Host ""
    Write-ColorOutput Red "Detalles del error:"
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, intente ejecutar nuevamente." -ForegroundColor Yellow
    
    Pause-Exit 15
    exit 1
}
