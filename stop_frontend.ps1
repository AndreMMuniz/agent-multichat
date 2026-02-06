# Stop Frontend Script
# Run: .\stop_frontend.ps1

Write-Host "Stopping Frontend (Streamlit)..." -ForegroundColor Yellow

# Find process on port 8501
$port = 8501
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($process) {
    Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
    Write-Host "Frontend server (PID: $process) stopped successfully." -ForegroundColor Green
}
else {
    Write-Host "No frontend server found running on port $port." -ForegroundColor Gray
}
