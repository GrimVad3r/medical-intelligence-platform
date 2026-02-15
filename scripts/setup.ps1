# Initial setup for Medical Intelligence Platform (Windows)
# Usage: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$VenvDir = if ($env:VENV_PATH) { $env:VENV_PATH } else { ".venv" }

Write-Host "Setup: Medical Intelligence Platform"
Write-Host "Project root: $ProjectRoot"

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtualenv at $VenvDir..."
    & $Python -m venv $VenvDir
}
& "$VenvDir\Scripts\Activate.ps1"

Write-Host "Upgrading pip and installing dependencies..."
pip install -U pip
pip install -r requirements.txt
if (Test-Path requirements-dev.txt) { pip install -r requirements-dev.txt }
if (Test-Path requirements-nlp.txt) { pip install -r requirements-nlp.txt }

if (-not (Test-Path .env) -and (Test-Path .env.example)) {
    Write-Host "Copying .env.example to .env..."
    Copy-Item .env.example .env
    Write-Host "Edit .env with your API keys and database URL."
}

Write-Host "Installing package in editable mode..."
pip install -e .

Write-Host "Setting up database..."
python scripts/setup_db.py
if ($LASTEXITCODE -ne 0) { Write-Error "DB setup failed (check DATABASE_URL in .env)" }

if ((Test-Path dbt) -and (Get-Command dbt -ErrorAction SilentlyContinue)) {
    Write-Host "Initializing dbt..."
    Push-Location dbt; dbt deps --profiles-dir . 2>$null; Pop-Location
}

Write-Host "Setup complete. Activate with: .\$VenvDir\Scripts\Activate.ps1"
