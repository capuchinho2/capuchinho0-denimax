# Script para instalar Denimax como servico do Windows
# Execute como Administrador

# Instalar NSSM (Non-Sucking Service Manager) se necessário
$nssmPath = "C:\nssm\nssm.exe"

if (-not (Test-Path $nssmPath)) {
    Write-Host "NSSM nao encontrado. Baixando..." -ForegroundColor Yellow
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $tempZip = "$env:TEMP\nssm.zip"
    $tempDir = "$env:TEMP\nssm"
    
    Invoke-WebRequest -Uri $nssmUrl -OutFile $tempZip
    Expand-Archive -Path $tempZip -DestinationPath $tempDir -Force
    
    New-Item -ItemType Directory -Path "C:\nssm" -Force | Out-Null
    Copy-Item "$tempDir\nssm-2.24\win64\nssm.exe" -Destination $nssmPath
    
    Remove-Item $tempZip -Force
    Remove-Item $tempDir -Recurse -Force
}

# Configurações
$serviceName = "DenimaxDashboard"
$projectPath = $PSScriptRoot
$pythonExe = Join-Path $projectPath "venv\Scripts\python.exe"
$scriptPath = "-m backend.app"

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Instalando Denimax como Servico Windows" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Verificar se o serviço já existe
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if ($existingService) {
    Write-Host "Servico ja existe. Removendo..." -ForegroundColor Yellow
    & $nssmPath stop $serviceName
    & $nssmPath remove $serviceName confirm
    Start-Sleep -Seconds 2
}

# Instalar o serviço
Write-Host "Instalando servico..." -ForegroundColor Green
& $nssmPath install $serviceName $pythonExe $scriptPath
& $nssmPath set $serviceName AppDirectory $projectPath
& $nssmPath set $serviceName DisplayName "Denimax Production Dashboard"
& $nssmPath set $serviceName Description "Dashboard de producao - Sistema Denimax"
& $nssmPath set $serviceName Start SERVICE_AUTO_START

# Configurar logs
$logsDir = Join-Path $projectPath "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

& $nssmPath set $serviceName AppStdout (Join-Path $logsDir "service.log")
& $nssmPath set $serviceName AppStderr (Join-Path $logsDir "service_error.log")

# Iniciar o serviço
Write-Host "`nIniciando servico..." -ForegroundColor Green
& $nssmPath start $serviceName

Start-Sleep -Seconds 3

# Verificar status
$service = Get-Service -Name $serviceName
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Status: " -NoNewline -ForegroundColor Cyan
if ($service.Status -eq 'Running') {
    Write-Host "RODANDO" -ForegroundColor Green
} else {
    Write-Host "PARADO" -ForegroundColor Red
}
Write-Host "================================================`n" -ForegroundColor Cyan

Write-Host "O servidor agora roda automaticamente!" -ForegroundColor Green
Write-Host "Acesse: http://localhost:5000" -ForegroundColor Yellow
Write-Host "`nComandos uteis:" -ForegroundColor Cyan
Write-Host "  Parar:     nssm stop $serviceName" -ForegroundColor White
Write-Host "  Iniciar:   nssm start $serviceName" -ForegroundColor White
Write-Host "  Remover:   nssm remove $serviceName" -ForegroundColor White
Write-Host "  Logs em:   $logsDir`n" -ForegroundColor White

Read-Host "Pressione ENTER para sair"
