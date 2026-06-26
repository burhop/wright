$ErrorActionPreference = "Stop"

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

function Set-HermesApiServerEnv {
    $settings = [ordered]@{
        "API_SERVER_ENABLED"  = "true"
        "API_SERVER_HOST"     = "127.0.0.1"
        "API_SERVER_PORT"     = "8642"
        "API_SERVER_KEY"      = "wright-local-dev"
        "HERMES_API_BASE_URL" = "http://127.0.0.1:8642"
        "HERMES_API_KEY"      = "wright-local-dev"
    }

    foreach ($entry in $settings.GetEnumerator()) {
        [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, "User")
        Set-Item -Path "env:$($entry.Key)" -Value $entry.Value
    }

    $hermesHome = Join-Path $env:USERPROFILE ".hermes"
    New-Item -ItemType Directory -Path $hermesHome -Force | Out-Null
    $envPath = Join-Path $hermesHome ".env"
    $lines = @()
    if (Test-Path $envPath) {
        $lines = Get-Content -Path $envPath
        foreach ($key in $settings.Keys) {
            $lines = @($lines | Where-Object { $_ -notmatch "^$([regex]::Escape($key))=" })
        }
    }
    foreach ($entry in $settings.GetEnumerator()) {
        $lines += "$($entry.Key)=$($entry.Value)"
    }
    Set-Content -Path $envPath -Value $lines -Encoding UTF8
}

function Get-ProcessTree {
    param([Parameter(Mandatory=$true)][int]$RootProcessId)

    $allProcesses = Get-CimInstance Win32_Process
    $processesByParent = $allProcesses | Group-Object ParentProcessId -AsHashTable -AsString
    $queue = New-Object System.Collections.Generic.Queue[int]
    $seen = New-Object 'System.Collections.Generic.HashSet[int]'
    $queue.Enqueue($RootProcessId)

    while ($queue.Count -gt 0) {
        $processId = $queue.Dequeue()
        if (-not $seen.Add($processId)) {
            continue
        }

        $process = $allProcesses | Where-Object { $_.ProcessId -eq $processId } | Select-Object -First 1
        if ($process) {
            $process
        }

        $children = $processesByParent[[string]$processId]
        if ($children) {
            foreach ($child in $children) {
                $queue.Enqueue([int]$child.ProcessId)
            }
        }
    }
}

function Stop-ProcessTree {
    param([Parameter(Mandatory=$true)][int]$RootProcessId)

    $tree = @(Get-ProcessTree -RootProcessId $RootProcessId)
    foreach ($process in ($tree | Sort-Object ProcessId -Descending)) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

if (-not $env:HERMES_SETUP_URL) {
    throw "HERMES_SETUP_URL is required."
}

$installTimeoutSeconds = 600
if ($env:HERMES_INSTALL_TIMEOUT_SECONDS) {
    $installTimeoutSeconds = [int]$env:HERMES_INSTALL_TIMEOUT_SECONDS
}

$setupArguments = "/S"
if ($env:HERMES_SETUP_ARGUMENTS) {
    $setupArguments = $env:HERMES_SETUP_ARGUMENTS
}

$setupPath = Join-Path $env:TEMP "Hermes-Setup.exe"
Write-Output "Downloading Hermes Desktop installer..."
Invoke-WebRequest -Uri $env:HERMES_SETUP_URL -OutFile $setupPath -UseBasicParsing

Write-Output "Installing Hermes Desktop with arguments: $setupArguments"
$process = Start-Process -FilePath $setupPath -ArgumentList $setupArguments -PassThru
if (-not $process.WaitForExit($installTimeoutSeconds * 1000)) {
    Write-Output "Hermes installer did not exit within $installTimeoutSeconds seconds."
    Write-Output "Installer process tree:"
    Get-ProcessTree -RootProcessId $process.Id |
        Select-Object ProcessId, ParentProcessId, Name, CommandLine |
        Format-List |
        Out-String |
        Write-Output
    Stop-ProcessTree -RootProcessId $process.Id
    throw "Hermes installer did not complete unattended. Provide supported silent arguments via -HermesSetupArguments or a non-interactive Hermes installer artifact."
}
Write-Output "Hermes installer exited with code $($process.ExitCode)."
if ($process.ExitCode -ne 0) {
    throw "Hermes installer failed with exit code $($process.ExitCode)."
}

$hermesExe = $null
for ($i = 1; $i -le 60; $i++) {
    $hermesExe = Find-HermesDesktopExe
    if ($hermesExe) {
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $hermesExe) {
    throw "Hermes.exe was not found after install."
}

Set-HermesApiServerEnv

$metadata = [ordered]@{
    image_role        = "wright-hermes-ready"
    created_utc       = (Get-Date).ToUniversalTime().ToString("o")
    hermes_exe        = $hermesExe
    hermes_setup_url  = $env:HERMES_SETUP_URL
    api_server_port   = 8642
    api_server_key_id = "wright-local-dev"
}
$metadataPath = "C:\wright-image-metadata.json"
$metadata | ConvertTo-Json | Set-Content -Path $metadataPath -Encoding UTF8

Write-Output "Hermes Desktop installed at $hermesExe."
Write-Output "Image metadata written to $metadataPath."
