# Script para renomear o backend de agente-escrita para agent-analyzer
# Execute este script DEPOIS de parar os servidores rodando

Write-Host "Renomeando backend: agente-escrita -> agent-analyzer" -ForegroundColor Cyan
Write-Host ""

$oldPath = "c:\Users\mandr\OneDrive\Documentos\Projeto\agente-escrita"
$newPath = "c:\Users\mandr\OneDrive\Documentos\Projeto\agent-analyzer"

# Verificar se o diretório antigo existe
if (Test-Path $oldPath) {
    Write-Host "1. Parando processos Python..." -ForegroundColor Yellow
    Get-Process | Where-Object { $_.Path -like "*agente-escrita*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    Write-Host "2. Renomeando diretorio..." -ForegroundColor Yellow
    Rename-Item -Path $oldPath -NewName "agent-analyzer" -ErrorAction Stop
    
    Write-Host ""
    Write-Host "OK - Backend renomeado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Novo caminho: $newPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Proximos passos:" -ForegroundColor Yellow
    Write-Host "1. cd agent-analyzer" -ForegroundColor White
    Write-Host "2. python main.py" -ForegroundColor White
}
else {
    Write-Host "ERRO: Diretorio nao encontrado: $oldPath" -ForegroundColor Red
}
