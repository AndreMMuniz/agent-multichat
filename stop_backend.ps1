# Stop Backend Script
# Run: .\stop_backend.ps1

Write-Host "Stopping Backend Server..." -ForegroundColor Yellow

# Find process on port 8000
$port = 8000
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($process) {
    Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
    Write-Host "Backend server (PID: $process) stopped successfully." -ForegroundColor Green
} else {
    Write-Host "No backend server found running on port $port." -ForegroundColor Gray
}
