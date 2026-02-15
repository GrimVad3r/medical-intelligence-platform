# Run pipeline stage: scrape | nlp | yolo | dbt | all
# Usage: .\scripts\run_pipeline.ps1 [stage]

param([string]$Stage = "all")

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

if (Test-Path .env) { Get-Content .env | ForEach-Object { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process') } } }
$VenvActivate = if ($env:VENV_PATH) { "$env:VENV_PATH\Scripts\Activate.ps1" } else { ".venv\Scripts\Activate.ps1" }
if (-not (Test-Path $VenvActivate)) { Write-Error "Virtualenv not found at $VenvActivate" }
& $VenvActivate

$LogDir = if ($env:LOG_DIR) { $env:LOG_DIR } else { "logs" }
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Log { param($Msg) $line = "[$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')] $Msg"; Write-Host $line; Add-Content -Path "$LogDir\pipeline.log" -Value $line }

function Run-Scrape {
    Log "Running Telegram scrape..."
    python scripts/scrape_telegram.py --nlp --limit $env:SCRAPE_LIMIT
    if ($LASTEXITCODE -ne 0) { throw "Scrape failed" }
}
function Run-Nlp {
    Log "Running NLP analysis..."
    python scripts/analyze_nlp.py --from-db --limit $env:NLP_LIMIT
    if ($LASTEXITCODE -ne 0) { throw "NLP failed" }
}
function Run-Yolo {
    if ($env:YOLO_INPUT -and (Test-Path $env:YOLO_INPUT)) {
        Log "Running YOLO analysis..."
        python scripts/analyze_yolo.py $env:YOLO_INPUT --save-db
        if ($LASTEXITCODE -ne 0) { throw "YOLO failed" }
    } else { Log "Skip YOLO: YOLO_INPUT not set or not a directory" }
}
function Run-Dbt {
    if ((Test-Path dbt) -and (Get-Command dbt -ErrorAction SilentlyContinue)) {
        Log "Running dbt..."
        Push-Location dbt; dbt run --profiles-dir .; Pop-Location
        if ($LASTEXITCODE -ne 0) { throw "dbt run failed" }
    } else { Log "Skip dbt: dbt project or CLI not found" }
}

switch ($Stage) {
    "scrape" { Run-Scrape }
    "nlp"    { Run-Nlp }
    "yolo"   { Run-Yolo }
    "dbt"    { Run-Dbt }
    "all"    { Run-Scrape; Run-Nlp; Run-Yolo; Run-Dbt }
    default  { Write-Host "Usage: $MyInvocation.MyCommand.Name {scrape|nlp|yolo|dbt|all}"; exit 1 }
}
Log "Pipeline stage '$Stage' completed."
