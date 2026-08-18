param(
    [switch]$SkipDocker,
    [ValidateRange(5, 300)]
    [int]$WaitSeconds = 60
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$runtimeRoot = Join-Path $env:LOCALAPPDATA "wright\startup"
$logRoot = Join-Path $runtimeRoot "logs"
$null = New-Item -ItemType Directory -Force -Path $logRoot
$lifecycleLog = Join-Path $logRoot "startup.log"

function Write-LifecycleLog {
    param([string]$Message)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -LiteralPath $lifecycleLog -Value "$timestamp $Message"
}

function Test-HttpEndpoint {
    param([string]$Uri)

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

function Wait-HttpEndpoint {
    param(
        [string]$Name,
        [string]$Uri,
        [int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if (Test-HttpEndpoint -Uri $Uri) {
            Write-LifecycleLog "$Name ready at $Uri"
            return $true
        }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    Write-LifecycleLog "$Name did not become ready at $Uri within ${TimeoutSeconds}s"
    return $false
}

function Start-HiddenProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory
    )

    $startParameters = @{
        FilePath = $FilePath
        ArgumentList = $ArgumentList
        WorkingDirectory = $WorkingDirectory
        WindowStyle = "Hidden"
        RedirectStandardOutput = (Join-Path $logRoot "$Name.out.log")
        RedirectStandardError = (Join-Path $logRoot "$Name.err.log")
        PassThru = $true
    }
    $process = Start-Process @startParameters
    Set-Content -LiteralPath (Join-Path $runtimeRoot "$Name.pid") -Value $process.Id
    Write-LifecycleLog "Started $Name as PID $($process.Id)"
}

Write-LifecycleLog "Startup check began from $repoRoot"

if (-not $SkipDocker) {
    $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    $dockerReady = Test-Path -LiteralPath "\\.\pipe\dockerDesktopLinuxEngine"

    if ($dockerReady) {
        Write-LifecycleLog "Docker engine already ready"
    }
    elseif (Test-Path -LiteralPath $dockerDesktop) {
        Start-Process -FilePath $dockerDesktop -ArgumentList "--minimized" -WindowStyle Hidden
        Write-LifecycleLog "Requested minimized Docker Desktop startup"
    }
    else {
        Write-LifecycleLog "Docker Desktop executable was not found"
    }
}

# The workstation runs Wright's complete local feature profile. These flags
# expose the routes and lifecycle controller; they do not eagerly launch the
# Rivet editor or its runner.
if ([string]::IsNullOrWhiteSpace($env:WRIGHT_AUTH_MODE)) {
    # This launcher binds only to loopback, so the normal local UI does not
    # require a Docker-style access token. Explicit enforced mode is preserved.
    $env:WRIGHT_AUTH_MODE = "compat"
}
$env:WRIGHT_RIVET_WORKFLOWS_ENABLED = "1"
$env:WRIGHT_RIVET_EDITOR_ENABLED = "1"
$env:WRIGHT_RIVET_AI_ENABLED = "1"
$env:WRIGHT_RIVET_RUNNER_ENABLED = "1"
$env:WRIGHT_RIVET_REAL_EXECUTION_ENABLED = "1"
$env:WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED = "1"
$env:WRIGHT_SURFACES_ENABLED = "1"
$env:WRIGHT_SURFACES_LIVE_APPS_ENABLED = "1"

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$apiUri = "http://127.0.0.1:8000/api/health"
if (Test-HttpEndpoint -Uri $apiUri) {
    Write-LifecycleLog "Wright API already ready at $apiUri"
}
elseif (Test-Path -LiteralPath $python) {
    Start-HiddenProcess -Name "wright-api" -FilePath $python -ArgumentList @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000") -WorkingDirectory $repoRoot
}
else {
    Write-LifecycleLog "Wright Python environment was not found at $python"
}

$webUri = "http://127.0.0.1:5173/"
if (Test-HttpEndpoint -Uri $webUri) {
    Write-LifecycleLog "Wright web UI already ready at $webUri"
}
else {
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    $vite = Join-Path $repoRoot "node_modules\vite\bin\vite.js"
    if ($null -ne $node -and (Test-Path -LiteralPath $vite)) {
        Start-HiddenProcess -Name "wright-web" -FilePath $node.Source -ArgumentList @($vite, "--host", "127.0.0.1", "--port", "5173", "--strictPort") -WorkingDirectory (Join-Path $repoRoot "apps\web")
    }
    else {
        Write-LifecycleLog "Node or Vite was not found; Node=$($null -ne $node), Vite=$(Test-Path -LiteralPath $vite)"
    }
}

$apiReady = Wait-HttpEndpoint -Name "Wright API" -Uri $apiUri -TimeoutSeconds $WaitSeconds
$webReady = Wait-HttpEndpoint -Name "Wright web UI" -Uri $webUri -TimeoutSeconds $WaitSeconds
if ($apiReady -and $webReady) {
    Write-LifecycleLog "Startup check completed successfully"
    exit 0
}

Write-LifecycleLog "Startup check completed with one or more unavailable services"
exit 1
