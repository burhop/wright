param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8771
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$datasetRepo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$datasetRun = Join-Path $datasetRepo ".local-run/feature-081-live"
$datasetLogs = Join-Path $datasetRun "logs"
$null = New-Item -ItemType Directory -Force -Path $datasetLogs
$datasetUrl = "http://127.0.0.1:$Port"
$datasetPython = Join-Path $datasetRepo ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $datasetPython)) {
    throw "The Wright development Python environment is missing. Run the repository dependency setup first."
}

$existingCampaign = $null
try { $existingCampaign = Invoke-RestMethod "$datasetUrl/api/status" -TimeoutSec 3 } catch {}
if ($existingCampaign) {
    if ($existingCampaign.campaign_id -ne "081-engineering-datasets-v1") {
        throw "Port $Port serves a different campaign. Select another port."
    }
    [pscustomobject]@{url=$datasetUrl;state="already_running";metrics=$existingCampaign.metrics} | ConvertTo-Json
    return
}
$datasetListener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($datasetListener) { throw "Port $Port is occupied by another service." }

$datasetStart = @{
    FilePath = $datasetPython
    ArgumentList = @("scripts/engineering_dataset_campaign.py", "serve", "--port", [string]$Port)
    WorkingDirectory = $datasetRepo
    WindowStyle = "Hidden"
    PassThru = $true
    RedirectStandardOutput = (Join-Path $datasetLogs "dataset-dashboard.stdout.log")
    RedirectStandardError = (Join-Path $datasetLogs "dataset-dashboard.stderr.log")
}
$datasetProcess = Start-Process @datasetStart
$datasetSession = [pscustomobject]@{
    url=$datasetUrl
    pid=$datasetProcess.Id
    creation_time=$datasetProcess.StartTime.ToUniversalTime().ToString("o")
    executable=$datasetProcess.Path
    started_at=[DateTime]::UtcNow.ToString("o")
    command="scripts/engineering_dataset_campaign.py serve --port $Port"
    state_path=(Join-Path $datasetRepo "artifacts/engineering-workflow-datasets")
    execution_worker_status="Observed separately in campaign-runner-state; this launcher starts the dashboard only"
}
# Keep ownership even if a cold post-reboot scan outlasts the readiness request.
$datasetSession | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $datasetRun "dataset-dashboard.session.json")
$datasetDeadline = (Get-Date).AddSeconds(60)
$datasetReady = $false
do {
    try {
        $datasetStatus = Invoke-RestMethod "$datasetUrl/api/status" -TimeoutSec 5
        $datasetReady = $datasetStatus.campaign_id -eq "081-engineering-datasets-v1"
    } catch {}
    if (-not $datasetReady) { Start-Sleep -Milliseconds 300 }
} while (-not $datasetReady -and (Get-Date) -lt $datasetDeadline)
if (-not $datasetReady) { throw "Dashboard readiness timed out; inspect its saved process identity and $datasetLogs before retrying." }
$datasetSession | ConvertTo-Json
