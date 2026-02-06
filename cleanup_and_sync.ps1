# Script de limpeza para o projeto agente-multichat

Write-Host "--- Iniciando limpeza do ambiente ---" -ForegroundColor Cyan

# 1. Remove caches do Python
Get-ChildItem -Path . -Include __pycache__ -Recurse | Remove-Item -Recurse -Force
Write-Host "[OK] Cache do Python removido." -ForegroundColor Green

# 2. Limpa arquivos de log (mantendo o arquivo, mas zerando o conteúdo)
if (Test-Path "agent_debug.log") {
    Clear-Content "agent_debug.log"
    Write-Host "[OK] Log de debug limpo." -ForegroundColor Green
}

# 3. Remove pastas de build do Next.js (opcional, descomente se necessário)
# if (Test-Path ".next") { Remove-Item -Recurse -Force ".next" }

# 4. Garante que o Git ignore o que não deve ser rastreado
git rm -r --cached agent_debug.log --ignore-unmatch
git rm -r --cached __pycache__/ --ignore-unmatch

Write-Host "--- Ambiente pronto para Commit ---" -ForegroundColor Cyan