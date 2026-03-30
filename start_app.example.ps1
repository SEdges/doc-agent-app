# ========================================
# Joern Docs Agent - Startup Script
# ========================================
#
# Usage:
# 1. Copy this file to start_app.ps1
# 2. Edit start_app.ps1, set your API Key at line 20
# 3. Run: .\start_app.ps1
#
# Note: start_app.ps1 is in .gitignore (won't be committed)
# ========================================

Write-Host "[START] Launching Joern Docs Agent..." -ForegroundColor Cyan

# 1. Set OpenAI API Key
# Replace the placeholder below with your actual API Key
$env:OPENAI_API_KEY = "sk-proj-eQEwQPKeSwHbV89gNjVfrRTcajPhCh4PsgGXbBdl1pxJ4rbkh1StdjDA25xZ4NfdTcl8SQzZl"

# Validate API Key
if ($env:OPENAI_API_KEY -like "*YOUR_API_KEY_HERE*") {
    Write-Host "[ERROR] Please set your OpenAI API Key first!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Steps:" -ForegroundColor Yellow
    Write-Host "  1. Copy start_app.example.ps1 to start_app.ps1" -ForegroundColor Yellow
    Write-Host "  2. Edit start_app.ps1 line 20, paste your API Key" -ForegroundColor Yellow
    Write-Host "  3. Save and run .\start_app.ps1" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "[OK] API Key set (last 4 chars: ...$($env:OPENAI_API_KEY.Substring($env:OPENAI_API_KEY.Length - 4)))" -ForegroundColor Green

# 2. Activate conda environment
Write-Host "[ENV] Activating conda environment: joern-docs" -ForegroundColor Cyan
conda activate joern-docs

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to activate conda environment 'joern-docs'" -ForegroundColor Red
    Write-Host "        Please create it first: conda create -n joern-docs python=3.10 -y" -ForegroundColor Yellow
    pause
    exit 1
}

# 3. Set working directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
Write-Host "[DIR] Working directory: $scriptDir" -ForegroundColor Cyan

# 4. Start Streamlit application
Write-Host ""
Write-Host "[RUN] Starting Streamlit app..." -ForegroundColor Green
Write-Host "      Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

streamlit run joern_doc_agent_app.py
