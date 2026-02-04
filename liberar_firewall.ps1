# Script para liberar a porta 5000 no Firewall do Windows
# EXECUTE COMO ADMINISTRADOR

Write-Host "Liberando porta 5000 no Firewall do Windows..." -ForegroundColor Cyan

try {
    # Verifica se a regra já existe
    $regra = Get-NetFirewallRule -DisplayName "Flask Dashboard - Porta 5000" -ErrorAction SilentlyContinue
    
    if ($regra) {
        Write-Host "Regra ja existe. Removendo para recriar..." -ForegroundColor Yellow
        Remove-NetFirewallRule -DisplayName "Flask Dashboard - Porta 5000"
    }
    
    # Cria a regra de firewall
    New-NetFirewallRule -DisplayName "Flask Dashboard - Porta 5000" `
                        -Direction Inbound `
                        -LocalPort 5000 `
                        -Protocol TCP `
                        -Action Allow `
                        -Profile Domain,Private `
                        -Description "Permite acesso ao dashboard Flask na porta 5000"
    
    Write-Host ""
    Write-Host "✓ Porta 5000 liberada com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Agora outros computadores podem acessar:" -ForegroundColor Cyan
    Write-Host "  http://10.215.15.81:5000" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "✗ Erro ao liberar porta:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Certifique-se de executar este script como Administrador" -ForegroundColor Yellow
}

Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
