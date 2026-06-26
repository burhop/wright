param(
    [string]$WrightDir = "C:\wright",
    [string]$LlmApiUrl = ""
)

$ErrorActionPreference = "Stop"

function Refresh-Path {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath;$env:USERPROFILE\.local\bin;$env:LOCALAPPDATA\uv\bin"
}

function Invoke-Native {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $FilePath @Arguments 2>&1 | ForEach-Object { Write-Output $_ }
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
        }
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Copy-DirectoryClean {
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination
    )

    if (Test-Path $Destination) {
        Remove-Item -Path $Destination -Recurse -Force
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
    Copy-Item -Path $Source -Destination $Destination -Recurse -Force
}

function Find-HermesDesktopExe {
    $roots = @(
        (Join-Path $env:LOCALAPPDATA "hermes"),
        (Join-Path $env:LOCALAPPDATA "Programs"),
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)}
    ) | Where-Object { $_ } | Select-Object -Unique

    foreach ($root in $roots) {
        if (Test-Path $root) {
            $match = Get-ChildItem -Path $root -Filter "Hermes.exe" -Recurse -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($match) {
                return $match.FullName
            }
        }
    }

    return $null
}

function Find-HermesAgentPython {
    $candidate = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\venv\Scripts\python.exe"
    if (Test-Path $candidate) {
        return $candidate
    }

    return $null
}

function Stop-ExistingWrightProcesses {
    param([string]$WrightDir)

    $escapedWrightDir = [regex]::Escape($WrightDir)
    $currentPid = $PID
    $processes = Get-CimInstance Win32_Process |
        Where-Object {
            $_.ProcessId -ne $currentPid -and
            (
                ($_.CommandLine -and $_.CommandLine -match $escapedWrightDir) -or
                ($_.ExecutablePath -and $_.ExecutablePath -match $escapedWrightDir)
            )
        }

    foreach ($process in $processes) {
        Write-Output "Stopping existing Wright process $($process.ProcessId): $($process.Name)"
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Set-TestEnvironment {
    param([string]$LlmApiUrl)

    $settings = [ordered]@{
        "WRIGHT_REPO_DIR"      = $WrightDir
        "WRIGHT_API_HOST"     = "0.0.0.0"
        "WRIGHT_UI_MODE"      = "browser"
        "HERMES_API_BASE_URL" = "http://127.0.0.1:8642"
        "HERMES_API_KEY"      = "wright-local-dev"
        "API_SERVER_ENABLED"  = "true"
        "API_SERVER_HOST"     = "127.0.0.1"
        "API_SERVER_PORT"     = "8642"
        "API_SERVER_KEY"      = "wright-local-dev"
    }

    foreach ($entry in $settings.GetEnumerator()) {
        [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, "User")
        Set-Item -Path "env:$($entry.Key)" -Value $entry.Value
    }

    if ($LlmApiUrl.Trim()) {
        [Environment]::SetEnvironmentVariable("LLM_API_URL", $LlmApiUrl, "User")
        Set-Item -Path "env:LLM_API_URL" -Value $LlmApiUrl
    } else {
        [Environment]::SetEnvironmentVariable("LLM_API_URL", $null, "User")
        Remove-Item -Path "env:LLM_API_URL" -ErrorAction SilentlyContinue
    }

    $hermesEnvContent = @(
        "API_SERVER_ENABLED=true",
        "API_SERVER_HOST=127.0.0.1",
        "API_SERVER_PORT=8642",
        "API_SERVER_KEY=wright-local-dev"
    )

    $hermesEnvPaths = @(
        (Join-Path $env:LOCALAPPDATA "hermes\.env"),
        (Join-Path $env:USERPROFILE ".hermes\.env")
    )
    foreach ($envPath in $hermesEnvPaths) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $envPath) -Force | Out-Null
        Set-Content -Path $envPath -Value $hermesEnvContent -Encoding UTF8
    }

    New-Item -ItemType Directory -Path "C:\tmp" -Force | Out-Null
    Invoke-Native git config --global user.email "wright-test@example.local"
    Invoke-Native git config --global user.name "Wright Test"
}

function Start-HermesGatewayForTest {
    param(
        [Parameter(Mandatory=$true)][string]$HermesPath,
        [Parameter(Mandatory=$true)][string]$WrightDir
    )

    try {
        Invoke-Native $HermesPath gateway install
        Write-Output "Hermes Gateway installed for background startup."
    } catch {
        Write-Warning "Hermes gateway install failed; starting gateway for the current test session. $($_.Exception.Message)"
        $tmpDir = Join-Path $WrightDir "tmp"
        New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
        $stdout = Join-Path $tmpDir "hermes-gateway.stdout.log"
        $stderr = Join-Path $tmpDir "hermes-gateway.stderr.log"
        $process = Start-Process `
            -FilePath $HermesPath `
            -ArgumentList @("gateway", "run") `
            -WorkingDirectory $WrightDir `
            -RedirectStandardOutput $stdout `
            -RedirectStandardError $stderr `
            -PassThru `
            -WindowStyle Hidden
        Set-Content -Path (Join-Path $tmpDir "hermes-gateway.pid") -Value $process.Id -Encoding UTF8
    }
}

Refresh-Path
Set-TestEnvironment -LlmApiUrl $LlmApiUrl

$archive = "C:\Users\Public\Downloads\wright.zip"
if (-not (Test-Path $archive)) {
    throw "Wright archive was not copied to $archive."
}

Stop-ExistingWrightProcesses -WrightDir $WrightDir

if (Test-Path $WrightDir) {
    Remove-Item -Path $WrightDir -Recurse -Force
}
New-Item -ItemType Directory -Path $WrightDir -Force | Out-Null
tar -xf $archive -C $WrightDir

Push-Location $WrightDir
try {
    Invoke-Native uv sync --all-packages --all-groups
    Invoke-Native npm install
    Invoke-Native npm run build --workspace=apps/web
    Invoke-Native npm run build:desktop --workspace=apps/web
} finally {
    Pop-Location
}

$pluginSource = Join-Path $WrightDir "hermes-plugin-wright"
if (-not (Test-Path $pluginSource)) {
    throw "Wright plugin source was not found at $pluginSource."
}

$pluginTargets = @(
    (Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\plugins\wright"),
    (Join-Path $env:USERPROFILE ".hermes\hermes-agent\plugins\wright")
)
foreach ($target in $pluginTargets) {
    Copy-DirectoryClean -Source $pluginSource -Destination $target
}

$staleTarget = Join-Path $env:USERPROFILE ".hermes\plugins\wright"
if (Test-Path $staleTarget) {
    Remove-Item -Path $staleTarget -Recurse -Force
}

$hermesExe = Find-HermesDesktopExe
if (-not $hermesExe) {
    throw "Hermes Desktop is not installed in the parent image."
}

$hermesPython = Find-HermesAgentPython
if (-not $hermesPython) {
    throw "Hermes agent Python was not found under the Hermes Desktop install."
}

Invoke-Native $hermesPython -m pip install "pyyaml>=6.0" "pydantic>=2.0" "httpx>=0.27" "structlog>=24.0"

New-Item -ItemType Directory -Path (Join-Path $WrightDir "tmp") -Force | Out-Null
Set-Content -Path (Join-Path $WrightDir "tmp\hermes-desktop-path.txt") -Value $hermesExe -Encoding UTF8
Set-Content -Path (Join-Path $WrightDir "tmp\hermes-agent-python-path.txt") -Value $hermesPython -Encoding UTF8

$hermes = Get-Command hermes -ErrorAction SilentlyContinue
if ($hermes) {
    Invoke-Native $hermes.Source plugins enable wright
    Start-HermesGatewayForTest -HermesPath $hermes.Source -WrightDir $WrightDir
    $pluginList = (& $hermes.Source plugins list 2>&1 | Out-String)
    Write-Output $pluginList
    if ($pluginList -notmatch "wright") {
        throw "Hermes CLI does not list the Wright plugin after install."
    }
    if ($pluginList -match "wright[\s\S]*not enabled") {
        throw "Hermes CLI still reports the Wright plugin as not enabled."
    }
} else {
    Write-Warning "Hermes CLI was not found on PATH; folder-level plugin verification will run next."
}

Write-Output "Wright installed for Hermes Desktop test."
