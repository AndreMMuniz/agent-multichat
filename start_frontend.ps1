# Frontend Quick Start Script
# Run: .\start_frontend.ps1

Write-Host "Starting Frontend..." -ForegroundColor Cyan

# Install dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
py -m pip install -r requirements.txt

# Run Streamlit
Write-Host "Launching Streamlit..." -ForegroundColor Green
py -m streamlit run frontend.py
