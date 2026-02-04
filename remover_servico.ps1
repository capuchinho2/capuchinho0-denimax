# Script para remover o servico Denimax
# Execute como Administrador

$serviceName = "DenimaxDashboard"
$nssmPath = "C:\nssm\nssm.exe"

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Removendo Servico Denimax" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

if (-not (Test-Path $nssmPath)) {
    Write-Host "NSSM nao encontrado em $nssmPath" -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"
    exit
}

$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "Servico nao encontrado." -ForegroundColor Yellow
    Read-Host "Pressione ENTER para sair"
    exit
}

Write-Host "Parando servico..." -ForegroundColor Yellow
& $nssmPath stop $serviceName
Start-Sleep -Seconds 2

Write-Host "Removendo servico..." -ForegroundColor Yellow
& $nssmPath remove $serviceName confirm

Write-Host "`nServico removido com sucesso!" -ForegroundColor Green
Write-Host "Agora voce pode usar o iniciar_servidor.bat normalmente.`n" -ForegroundColor Cyan

Read-Host "Pressione ENTER para sair"
