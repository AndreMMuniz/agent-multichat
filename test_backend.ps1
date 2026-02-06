# Backend Test Script
# Run: .\test_backend.ps1

Write-Host "Testing Backend - Log Analysis Agent" -ForegroundColor Cyan
Write-Host ""

# Test 1: Verify server
Write-Host "1. Verifying FastAPI server..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/docs" -Method GET -ErrorAction Stop | Out-Null
    Write-Host "   OK - Server running" -ForegroundColor Green
}
catch {
    Write-Host "   ERROR - Server is not responding!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Log Analysis (SSH Error)
Write-Host "2. Testing log analysis (SSH Error)..." -ForegroundColor Yellow
$logTest1 = @{
    topic = "ERROR: Permission denied (publickey) for git@github.com"
} | ConvertTo-Json

$response1 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/write" `
    -Method POST `
    -ContentType "application/json" `
    -Body $logTest1

Write-Host "   Status: $($response1.status)" -ForegroundColor Cyan
Write-Host "   Is Safe: $($response1.is_safe)" -ForegroundColor Green
Write-Host "   Diagnosis: $($response1.diagnosis.Substring(0, [Math]::Min(100, $response1.diagnosis.Length)))..." -ForegroundColor Gray
Write-Host ""

Start-Sleep -Seconds 2

# Test 3: Log Analysis (Coolify Error)
Write-Host "3. Testing log analysis (Coolify Error)..." -ForegroundColor Yellow
$logTest2 = @{
    topic = "ERROR: fatal: Could not read from remote repository"
} | ConvertTo-Json

$response2 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/write" `
    -Method POST `
    -ContentType "application/json" `
    -Body $logTest2

Write-Host "   Status: $($response2.status)" -ForegroundColor Cyan
Write-Host "   Is Safe: $($response2.is_safe)" -ForegroundColor Green
Write-Host ""

# Test 4: History
Write-Host "4. Testing /history endpoint..." -ForegroundColor Yellow
$history = Invoke-RestMethod -Uri "http://127.0.0.1:8000/history" -Method GET

if ($history.Count -gt 0) {
    Write-Host "   OK - $($history.Count) record(s) found" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Latest analyses:" -ForegroundColor Cyan
    foreach ($record in $history | Select-Object -First 3) {
        Write-Host "   ----------------------------------------" -ForegroundColor DarkGray
        Write-Host "   ID: $($record.id) | Timestamp: $($record.timestamp)" -ForegroundColor Gray
        Write-Host "   Safe: $($record.is_safe) | Processing: $($record.processing_time_ms)ms" -ForegroundColor Gray
    }
}
else {
    Write-Host "   History empty (no analyses saved yet)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tests completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Available Endpoints:" -ForegroundColor Cyan
Write-Host "  POST http://127.0.0.1:8000/write" -ForegroundColor White
Write-Host "  GET  http://127.0.0.1:8000/history" -ForegroundColor White
Write-Host "  GET  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Next step: Connect to Next.js frontend!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
