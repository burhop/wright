# Fast in-place update for an already-created Wright + Hermes VM.
#
# This avoids the full provisioning loop. It copies only the current Wright
# plugin files and patches Hermes config/env values inside the running VM.
#
# Run from an Administrator PowerShell on the Windows host:
#   .\update-running-vm.ps1

param(
    [string]$VmName = "Wright-Hermes-Sandbox",
    [string]$Username = "User",
    [string]$Password = "password",
    [string]$WrightDir = "C:\wright",
    [string]$LlmApiUrl = "http://192.168.1.165:8000/v1"
)

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Output "Restarting this script as Administrator..."
    $argList = @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "`"$PSCommandPath`""
    )
    foreach ($entry in $PSBoundParameters.GetEnumerator()) {
        $argList += "-$($entry.Key)"
        $argList += "`"$($entry.Value)`""
    }
    Start-Process powershell.exe -Verb RunAs -ArgumentList $argList
    Exit 0
}

if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: Hyper-V PowerShell cmdlets are not available."
    Exit 1
}

$vm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
if (-not $vm) {
    Write-Error "ERROR: VM '$VmName' was not found."
    Exit 1
}

if ($vm.State -ne "Running") {
    Start-VM -Name $VmName
    Write-Output "Started VM '$VmName'. Waiting for guest..."
    Start-Sleep -Seconds 5
}

$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ($Username, $securePassword)

$workspaceDir = (Get-Item $PSScriptRoot).Parent.FullName
$pluginSource = Join-Path $workspaceDir "hermes-plugin-wright"
$guestPluginZip = "C:\Users\Public\Downloads\wright-plugin-hot-update.zip"
$hostPluginZip = Join-Path $env:TEMP "wright-plugin-hot-update.zip"
$guestRepoZip = "C:\Users\Public\Downloads\wright-repo-hot-update.zip"
$hostRepoZip = Join-Path $env:TEMP "wright-repo-hot-update.zip"

if (Test-Path $hostPluginZip) {
    Remove-Item $hostPluginZip -Force
}
if (Test-Path $hostRepoZip) {
    Remove-Item $hostRepoZip -Force
}

Write-Output "Preparing plugin hot-update archive..."
Push-Location $pluginSource
tar -cf $hostPluginZip .
Pop-Location

Write-Output "Preparing repo source hot-update archive..."
Push-Location $workspaceDir
tar -cf $hostRepoZip `
    --exclude="node_modules" `
    --exclude=".venv" `
    --exclude=".git" `
    --exclude="windows-sandbox/.vm" `
    --exclude="tmp" `
    --exclude="*.log" `
    --exclude="*.pid" `
    --exclude="*.db" `
    --exclude="*.db-journal" `
    --exclude="*.db-wal" `
    --exclude="*.db-shm" `
    .
Pop-Location

Write-Output "Copying plugin archive into VM..."
Copy-VMFile -VMName $VmName -SourcePath $hostPluginZip -DestinationPath $guestPluginZip -CreateFullPath -FileSource Host -Force
Remove-Item $hostPluginZip -Force -ErrorAction SilentlyContinue

Write-Output "Copying repo source archive into VM..."
Copy-VMFile -VMName $VmName -SourcePath $hostRepoZip -DestinationPath $guestRepoZip -CreateFullPath -FileSource Host -Force
Remove-Item $hostRepoZip -Force -ErrorAction SilentlyContinue

Write-Output "Patching running VM..."
Invoke-Command -VMName $VmName -Credential $cred -ArgumentList $guestPluginZip, $guestRepoZip, $WrightDir, $LlmApiUrl -ScriptBlock {
    param($GuestPluginZip, $GuestRepoZip, $WrightDir, $LlmApiUrl)

    $ErrorActionPreference = "Stop"

    function Copy-DirectoryClean {
        param(
            [Parameter(Mandatory=$true)][string]$Source,
            [Parameter(Mandatory=$true)][string]$Destination
        )

        if (Test-Path $Destination) {
            Remove-Item $Destination -Force -Recurse -ErrorAction SilentlyContinue
        }
        $parent = Split-Path -Parent $Destination
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        Copy-Item -Path $Source -Destination $Destination -Recurse -Force | Out-Null
    }

    function Patch-HermesConfig {
        param([string]$Path)

        $parent = Split-Path -Parent $Path
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }

        $text = ""
        if (Test-Path $Path) {
            $text = Get-Content -Path $Path -Raw
            $text = $text.Replace("/home/burhop/repos/wright", $WrightDir)
            $text = $text.Replace("\\home\\burhop\\repos\\wright", $WrightDir)
        }

        if ($text -notmatch "mcp_servers:") {
            $text += @"

mcp_servers:
  wrightgateway:
    command: uv
    args:
      - run
      - --project
      - $WrightDir
      - python
      - -m
      - api.gateway
"@
        } elseif ($text -notmatch [regex]::Escape($WrightDir)) {
            $text += @"

# Wright hot-update path correction
# Ensure Hermes uses the VM-local Wright checkout.
"@
        }

        if ($text -notmatch "plugins:") {
            $text += @"

plugins:
  enabled:
    - wright
"@
        } elseif ($text -notmatch "wright") {
            $text += @"

# Wright hot-update plugin enable marker
"@
        }

        Set-Content -Path $Path -Value $text -Encoding UTF8
    }

    function Invoke-NativeFileRedirect {
        param(
            [Parameter(Mandatory=$true)][string]$FilePath,
            [string[]]$ArgumentList = @(),
            [string]$Description = "native command",
            [switch]$WarnOnly
        )

        Write-Output $Description
        $stdoutPath = Join-Path $env:TEMP ("wright-hot-update-out-{0}.txt" -f ([guid]::NewGuid()))
        $stderrPath = Join-Path $env:TEMP ("wright-hot-update-err-{0}.txt" -f ([guid]::NewGuid()))

        try {
            $proc = Start-Process `
                -FilePath $FilePath `
                -ArgumentList $ArgumentList `
                -NoNewWindow `
                -Wait `
                -PassThru `
                -RedirectStandardOutput $stdoutPath `
                -RedirectStandardError $stderrPath

            if (Test-Path $stdoutPath) {
                Get-Content -Path $stdoutPath -ErrorAction SilentlyContinue | ForEach-Object { Write-Output $_ }
            }
            if (Test-Path $stderrPath) {
                Get-Content -Path $stderrPath -ErrorAction SilentlyContinue | ForEach-Object { Write-Output $_ }
            }

            if ($proc.ExitCode -ne 0) {
                $message = "$Description failed with exit code $($proc.ExitCode)."
                if ($WarnOnly) {
                    Write-Warning $message
                } else {
                    Write-Error "ERROR: $message"
                    Exit 1
                }
            }
        } finally {
            Remove-Item $stdoutPath -Force -ErrorAction SilentlyContinue
            Remove-Item $stderrPath -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Output "Stopping Hermes Desktop and old Wright backend..."
    Get-Process -Name Hermes -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    $pidPath = Join-Path $WrightDir "tmp\wright-api.pid"
    if (Test-Path $pidPath) {
        $pidText = (Get-Content -Path $pidPath -Raw).Trim()
        if ($pidText -match '^\d+$') {
            taskkill /PID $pidText /F 2>$null | Out-Null
        }
        Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
    }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine.Contains($WrightDir) -and
            (
                $_.CommandLine -match "uvicorn" -or
                $_.CommandLine -match "api\.main:app" -or
                $_.CommandLine -match "apps\\api"
            )
        } |
        ForEach-Object {
            Write-Output "Stopping Wright backend process $($_.ProcessId): $($_.Name)"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
    Start-Sleep -Seconds 1

    Write-Output "Overlaying current repo source into $WrightDir..."
    if (-not (Test-Path $WrightDir)) {
        New-Item -ItemType Directory -Path $WrightDir -Force | Out-Null
    }
    tar -xf $GuestRepoZip -C $WrightDir 2>&1 | Write-Output
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Repo overlay reported warnings. Continuing; runtime logs/state files are intentionally ignored."
    }

    $unpackDir = "C:\Users\Public\Downloads\wright-plugin-hot-update"
    if (Test-Path $unpackDir) {
        Remove-Item $unpackDir -Force -Recurse -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Path $unpackDir -Force | Out-Null
    tar -xf $GuestPluginZip -C $unpackDir

    $targets = @(
        (Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\plugins\wright"),
        (Join-Path $env:USERPROFILE ".hermes\hermes-agent\plugins\wright")
    )
    foreach ($target in $targets) {
        Write-Output "Copying plugin to $target"
        Copy-DirectoryClean -Source $unpackDir -Destination $target
    }

    $staleUserPlugin = Join-Path $env:USERPROFILE ".hermes\plugins\wright"
    if (Test-Path $staleUserPlugin) {
        Remove-Item $staleUserPlugin -Force -Recurse -ErrorAction SilentlyContinue
    }

    [Environment]::SetEnvironmentVariable("WRIGHT_REPO_DIR", $WrightDir, "User")
    [Environment]::SetEnvironmentVariable("WRIGHT_API_HOST", "0.0.0.0", "User")
    [Environment]::SetEnvironmentVariable("WRIGHT_UI_MODE", "browser", "User")
    [Environment]::SetEnvironmentVariable("HERMES_API_BASE_URL", "http://127.0.0.1:8642", "User")
    [Environment]::SetEnvironmentVariable("HERMES_API_KEY", "wright-local-dev", "User")
    [Environment]::SetEnvironmentVariable("API_SERVER_ENABLED", "true", "User")
    [Environment]::SetEnvironmentVariable("API_SERVER_HOST", "127.0.0.1", "User")
    [Environment]::SetEnvironmentVariable("API_SERVER_PORT", "8642", "User")
    [Environment]::SetEnvironmentVariable("API_SERVER_KEY", "wright-local-dev", "User")
    [Environment]::SetEnvironmentVariable("LLM_API_URL", $LlmApiUrl, "User")

    $env:WRIGHT_REPO_DIR = $WrightDir
    $env:WRIGHT_API_HOST = "0.0.0.0"
    $env:WRIGHT_UI_MODE = "browser"
    $env:HERMES_API_BASE_URL = "http://127.0.0.1:8642"
    $env:HERMES_API_KEY = "wright-local-dev"
    $env:API_SERVER_ENABLED = "true"
    $env:API_SERVER_HOST = "127.0.0.1"
    $env:API_SERVER_PORT = "8642"
    $env:API_SERVER_KEY = "wright-local-dev"
    $env:LLM_API_URL = $LlmApiUrl

    $llmHealthUrl = $LlmApiUrl.TrimEnd("/")
    if ($llmHealthUrl.EndsWith("/v1")) {
        $llmHealthUrl = $llmHealthUrl.Substring(0, $llmHealthUrl.Length - 3)
    }
    $llmHealthUrl = "$($llmHealthUrl.TrimEnd('/'))/health"
    [Environment]::SetEnvironmentVariable("LLM_HEALTH_URL", $llmHealthUrl, "User")
    $env:LLM_HEALTH_URL = $llmHealthUrl

    $wrightStateDb = Join-Path $WrightDir "apps\api\state.db"
    $stateParent = Split-Path -Parent $wrightStateDb
    if (-not (Test-Path $stateParent)) {
        New-Item -ItemType Directory -Path $stateParent -Force | Out-Null
    }
    $setLlmPy = @"
import sqlite3
db_path = r'''$wrightStateDb'''
llm_api_url = r'''$LlmApiUrl'''
conn = sqlite3.connect(db_path)
try:
    conn.execute("CREATE TABLE IF NOT EXISTS system_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES ('llm_api_url', ?)", (llm_api_url,))
    conn.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES ('active_agent', 'hermes')")
    conn.commit()
finally:
    conn.close()
"@
    $setLlmScript = Join-Path $env:TEMP "wright-set-llm-config.py"
    Set-Content -Path $setLlmScript -Value $setLlmPy -Encoding UTF8
    python $setLlmScript | Write-Output
    Remove-Item $setLlmScript -Force -ErrorAction SilentlyContinue

    $hermesHome = Join-Path $env:USERPROFILE ".hermes"
    if (-not (Test-Path $hermesHome)) {
        New-Item -ItemType Directory -Path $hermesHome -Force | Out-Null
    }
    $hermesEnvPath = Join-Path $hermesHome ".env"
    $apiEnv = [ordered]@{
        "API_SERVER_ENABLED" = "true"
        "API_SERVER_HOST" = "127.0.0.1"
        "API_SERVER_PORT" = "8642"
        "API_SERVER_KEY" = "wright-local-dev"
    }
    $envLines = @()
    if (Test-Path $hermesEnvPath) {
        $envLines = Get-Content -Path $hermesEnvPath
        foreach ($key in $apiEnv.Keys) {
            $envLines = @($envLines | Where-Object { $_ -notmatch "^$([regex]::Escape($key))=" })
        }
    }
    foreach ($entry in $apiEnv.GetEnumerator()) {
        $envLines += "$($entry.Key)=$($entry.Value)"
    }
    Set-Content -Path $hermesEnvPath -Value $envLines -Encoding UTF8

    $configPaths = @(
        (Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\config.yaml"),
        (Join-Path $env:USERPROFILE ".hermes\config.yaml"),
        (Join-Path $env:USERPROFILE ".hermes\profiles\wright\config.yaml")
    )
    foreach ($path in $configPaths) {
        Write-Output "Patching Hermes config $path"
        Patch-HermesConfig -Path $path
    }

    Write-Output "Refreshing Python workspace packages without reinstalling Node dependencies..."
    Push-Location $WrightDir
    $uvPath = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvPath) {
        Invoke-NativeFileRedirect `
            -FilePath $uvPath.Source `
            -ArgumentList @("sync", "--all-packages", "--all-groups") `
            -Description "uv sync --all-packages --all-groups" `
            -WarnOnly
    } else {
        Write-Warning "uv was not found on PATH; skipped Python workspace refresh."
    }
    Pop-Location

    $hermesPath = Get-Command hermes -ErrorAction SilentlyContinue
    if ($hermesPath) {
        Invoke-NativeFileRedirect `
            -FilePath $hermesPath.Source `
            -ArgumentList @("plugins", "enable", "wright") `
            -Description "Enabling Wright plugin..." `
            -WarnOnly
        Write-Output "Starting Hermes gateway with API server enabled..."
        $gatewayTaskName = "LaunchHermesGateway"
        Get-ScheduledTask -TaskName $gatewayTaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
        $gatewayAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"set `"HERMES_ACCEPT_HOOKS=1`" && set `"API_SERVER_ENABLED=true`" && set `"API_SERVER_HOST=127.0.0.1`" && set `"API_SERVER_PORT=8642`" && set `"API_SERVER_KEY=wright-local-dev`" && `"$($hermesPath.Source)`" gateway`""
        $gatewayPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
        Register-ScheduledTask -TaskName $gatewayTaskName -Action $gatewayAction -Principal $gatewayPrincipal | Out-Null
        Start-ScheduledTask -TaskName $gatewayTaskName
    } else {
        Write-Warning "Hermes CLI was not found on PATH."
    }

    $hermesExe = Get-ChildItem -Path "$env:LOCALAPPDATA\hermes", "$env:LOCALAPPDATA\Programs", "$env:ProgramFiles" -Filter "Hermes.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hermesExe) {
        Write-Output "Restarting Hermes Desktop in the interactive session: $($hermesExe.FullName)"
        $desktopTaskName = "LaunchHermesDesktop"
        Get-ScheduledTask -TaskName $desktopTaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
        $desktopAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"set `"WRIGHT_REPO_DIR=$WrightDir`" && set `"WRIGHT_API_HOST=0.0.0.0`" && set `"WRIGHT_UI_MODE=browser`" && set `"HERMES_API_BASE_URL=http://127.0.0.1:8642`" && set `"HERMES_API_KEY=wright-local-dev`" && set `"API_SERVER_ENABLED=true`" && set `"API_SERVER_KEY=wright-local-dev`" && set `"LLM_API_URL=$LlmApiUrl`" && start `"`" `"$($hermesExe.FullName)`"`""
        $desktopPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
        Register-ScheduledTask -TaskName $desktopTaskName -Action $desktopAction -Principal $desktopPrincipal | Out-Null
        Start-ScheduledTask -TaskName $desktopTaskName
    } else {
        Write-Warning "Hermes.exe was not found."
    }

    Write-Output "Hot update complete."
    Write-Output "WRIGHT_REPO_DIR=$env:WRIGHT_REPO_DIR"
    Write-Output "WRIGHT_UI_MODE=$env:WRIGHT_UI_MODE"
    Write-Output "HERMES_API_BASE_URL=$env:HERMES_API_BASE_URL"
}

Write-Output "Refreshing host port forwarding..."
$manageScript = Join-Path $PSScriptRoot "manage-vm.ps1"
& $manageScript expose -VmName $VmName

Write-Output ""
Write-Output "Running VM hot update complete."
Write-Output "In Hermes Desktop, run: /wright start"
Write-Output "Then check: http://127.0.0.1:18000/api/agent/health"
