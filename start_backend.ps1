
# Backend Quick Start Script
# Run: .\start_backend.ps1

Write-Host "Starting Backend - Multichat Agent" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check PostgreSQL
Write-Host "Checking PostgreSQL..." -ForegroundColor Yellow
$postgres = docker ps --filter "name=log_postgres" --format "{{.Names}}"

if ($postgres -eq "log_postgres") {
    Write-Host "PostgreSQL is already running" -ForegroundColor Green
}
else {
    Write-Host "PostgreSQL not found. Creating container..." -ForegroundColor Yellow
    docker run -d --name log_postgres -p 5433:5432 -e POSTGRES_USER=log_user -e POSTGRES_PASSWORD=password123 -e POSTGRES_DB=log_analyzer_db postgres:15-alpine
    
    Write-Host "PostgreSQL started on port 5433" -ForegroundColor Green
    Start-Sleep -Seconds 3
}

Write-Host ""

# Step 2: Test database connection
Write-Host "Testing database connection..." -ForegroundColor Yellow

# Ensure imports from root work
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
python tests\test_new_tables.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Database connected and tables created" -ForegroundColor Green
}
else {
    Write-Host "Error connecting to database" -ForegroundColor Red
    exit 1
}

Write-Host ""


# Step 3: Start FastAPI server
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
Write-Host "Backend available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

python main.py
