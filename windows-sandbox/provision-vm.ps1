# Hyper-V VM Provisioning: Wright + Hermes Desktop (User Install)
# ================================================================
# Simulates a real end-user setup -- no repo cloning for development,
# just standard package installs (uv tool install, npm install, etc).
#
# Run this ONCE inside a fresh Windows 11 Hyper-V VM. After it
# completes, take a VM checkpoint so you never need to run it again.
#
# Usage (inside the VM, as Administrator):
#   Set-ExecutionPolicy Bypass -Scope Process -Force
#   .\provision-vm.ps1
#
# After provisioning:
#   .\provision-vm.ps1 -StartServers

param(
    [switch]$SkipTools,      # Skip tool installation (if already done)
    [switch]$SkipWright,     # Skip Wright install
    [switch]$SkipDesktop,    # Skip Hermes Desktop setup
    [switch]$StartServers,   # Start Wright + open Hermes Desktop
    [string]$LlmApiUrl = "http://192.168.1.165:8000/v1",
    [string]$HermesSetupUrl = "https://hermes-assets.nousresearch.com/Hermes-Setup.exe"
)

$ErrorActionPreference = "Continue"
$WrightDir = "C:\wright"
$HermesDesktopDir = "C:\hermes-desktop"

# ---- Robust PATH management -----------------------------------------
# Single function that rebuilds PATH from the registry and discovers
# tool-specific directories dynamically. Called after every install step.
function Refresh-Path {
    # Start from the authoritative Machine + User registry values
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    # Chocolatey: prefer ChocolateyInstall env var, fall back to searching
    $chocoRoot = [System.Environment]::GetEnvironmentVariable("ChocolateyInstall","Machine")
    if (-not $chocoRoot) { $chocoRoot = [System.Environment]::GetEnvironmentVariable("ChocolateyInstall","User") }
    if (-not $chocoRoot) { $chocoRoot = $env:ChocolateyInstall }
    if (-not $chocoRoot) {
        # Env var not set -- search for choco.exe in common install locations
        foreach ($guess in @(
            "$env:ProgramData\chocolatey",
            "$env:SystemDrive\ProgramData\chocolatey",
            "$env:USERPROFILE\chocolatey"
        )) {
            if (Test-Path (Join-Path $guess "bin\choco.exe")) {
                $chocoRoot = $guess
                break
            }
        }
    }
    if ($chocoRoot) {
        $chocoBin = Join-Path $chocoRoot "bin"
        if ((Test-Path $chocoBin) -and ($env:Path -notlike "*$chocoBin*")) {
            $env:Path = "$chocoBin;$env:Path"
        }
    }

    # uv: check all known install locations
    foreach ($candidate in @(
        (Join-Path $env:USERPROFILE ".local\bin"),
        (Join-Path $env:USERPROFILE ".cargo\bin"),
        (Join-Path $env:LOCALAPPDATA "uv\bin")
    )) {
        if ((Test-Path $candidate) -and ($env:Path -notlike "*$candidate*")) {
            $env:Path = "$candidate;$env:Path"
        }
    }
}

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

function Get-HermesDesktopAgentPython {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\venv\Scripts\python.exe"),
        (Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\.venv\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

function Find-HermesDesktopExe {
    $searchRoots = @(
        (Join-Path $env:LOCALAPPDATA "hermes"),
        (Join-Path $env:LOCALAPPDATA "Programs"),
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)}
    )

    $userRoot = Join-Path $env:SystemDrive "Users"
    if (Test-Path $userRoot) {
        Get-ChildItem -Path $userRoot -Directory -ErrorAction SilentlyContinue |
            ForEach-Object {
                $searchRoots += (Join-Path $_.FullName "AppData\Local\hermes")
                $searchRoots += (Join-Path $_.FullName "AppData\Local\Programs")
            }
    }

    foreach ($root in ($searchRoots | Where-Object { $_ } | Select-Object -Unique)) {
        if (-not (Test-Path $root)) {
            continue
        }
        $candidate = Get-ChildItem -Path $root -Filter "Hermes.exe" -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($candidate) {
            return $candidate
        }
    }

    return $null
}

function Install-WrightPluginForHermes {
    param(
        [Parameter(Mandatory=$true)][string]$WrightDir
    )

    Write-Output "Installing Wright plugin into Hermes load locations..."
    $source = Join-Path $WrightDir "hermes-plugin-wright"
    if (-not (Test-Path $source)) {
        Write-Error "ERROR: Wright plugin source not found: $source"
        Exit 1
    }

    $pluginTargets = @(
        (Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\plugins\wright"),
        (Join-Path $env:USERPROFILE ".hermes\hermes-agent\plugins\wright")
    )

    $stalePluginTargets = @(
        (Join-Path $env:USERPROFILE ".hermes\plugins\wright")
    )

    foreach ($target in $pluginTargets) {
        Write-Output "  Copying plugin to $target"
        Copy-DirectoryClean -Source $source -Destination $target
    }
    foreach ($target in $stalePluginTargets) {
        if (Test-Path $target) {
            Write-Output "  Removing stale duplicate plugin copy at $target"
            Remove-Item $target -Force -Recurse -ErrorAction SilentlyContinue
        }
    }

    $desktopPython = Get-HermesDesktopAgentPython
    if ($desktopPython) {
        Write-Output "  Installing plugin dependencies into Hermes Desktop agent venv..."
        $uvPath = Get-Command uv -ErrorAction SilentlyContinue
        if ($uvPath) {
            & $uvPath.Source pip install --python $desktopPython --upgrade pyyaml pydantic httpx structlog | Write-Output
            & $uvPath.Source pip install --python $desktopPython --force-reinstall $source | Write-Output
        } else {
            & $desktopPython -m ensurepip --upgrade | Write-Output
            & $desktopPython -m pip install --upgrade pip | Write-Output
            & $desktopPython -m pip install --upgrade pyyaml pydantic httpx structlog | Write-Output
            & $desktopPython -m pip install --force-reinstall $source | Write-Output
        }
        & $desktopPython -c "import httpx, structlog, yaml, pydantic; import hermes_plugin_wright.commands" | Write-Output
        if ($LASTEXITCODE -ne 0) {
            Write-Error "ERROR: Wright plugin dependencies could not be imported by Hermes Desktop agent Python."
            Exit 1
        }
        & $desktopPython -c "import importlib.metadata as m; assert any(ep.name == 'wright' for ep in m.entry_points(group='hermes_agent.plugins'))" | Write-Output
        if ($LASTEXITCODE -ne 0) {
            Write-Error "ERROR: Hermes Desktop agent Python cannot discover the Wright plugin entry point."
            Exit 1
        }
        $activeInit = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\plugins\wright\__init__.py"
        & $desktopPython -c "import importlib.util, sys; p = r'$activeInit'; spec = importlib.util.spec_from_file_location('wright_flat_verify', p, submodule_search_locations=[__import__('os').path.dirname(p)]); m = importlib.util.module_from_spec(spec); sys.modules['wright_flat_verify'] = m; spec.loader.exec_module(m); assert hasattr(m, 'register')" | Write-Output
        if ($LASTEXITCODE -ne 0) {
            Write-Error "ERROR: Active flat Wright plugin directory cannot be imported by Hermes Desktop agent Python."
            Exit 1
        }
    } else {
        Write-Warning "Hermes Desktop agent venv python not found; plugin folder copies were still installed."
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
    Set-WrightLlmConfig -WrightDir $WrightDir -LlmApiUrl $LlmApiUrl
}

function Set-HermesApiServerEnv {
    [Environment]::SetEnvironmentVariable("API_SERVER_ENABLED", "true", "User")
    [Environment]::SetEnvironmentVariable("API_SERVER_HOST", "127.0.0.1", "User")
    [Environment]::SetEnvironmentVariable("API_SERVER_PORT", "8642", "User")
    [Environment]::SetEnvironmentVariable("API_SERVER_KEY", "wright-local-dev", "User")
    [Environment]::SetEnvironmentVariable("HERMES_API_BASE_URL", "http://127.0.0.1:8642", "User")
    [Environment]::SetEnvironmentVariable("HERMES_API_KEY", "wright-local-dev", "User")
    $env:API_SERVER_ENABLED = "true"
    $env:API_SERVER_HOST = "127.0.0.1"
    $env:API_SERVER_PORT = "8642"
    $env:API_SERVER_KEY = "wright-local-dev"
    $env:HERMES_API_BASE_URL = "http://127.0.0.1:8642"
    $env:HERMES_API_KEY = "wright-local-dev"

    $hermesHome = Join-Path $env:USERPROFILE ".hermes"
    if (-not (Test-Path $hermesHome)) {
        New-Item -ItemType Directory -Path $hermesHome -Force | Out-Null
    }
    $envPath = Join-Path $hermesHome ".env"
    $values = [ordered]@{
        "API_SERVER_ENABLED" = "true"
        "API_SERVER_HOST" = "127.0.0.1"
        "API_SERVER_PORT" = "8642"
        "API_SERVER_KEY" = "wright-local-dev"
    }
    $lines = @()
    if (Test-Path $envPath) {
        $lines = Get-Content -Path $envPath
        foreach ($key in $values.Keys) {
            $lines = @($lines | Where-Object { $_ -notmatch "^$([regex]::Escape($key))=" })
        }
    }
    foreach ($entry in $values.GetEnumerator()) {
        $lines += "$($entry.Key)=$($entry.Value)"
    }
    Set-Content -Path $envPath -Value $lines -Encoding UTF8
}

function Test-HermesDesktopInstall {
    $hermesExe = Find-HermesDesktopExe
    if (-not $hermesExe) {
        Write-Error "ERROR: Hermes.exe was not found after installation."
        Exit 1
    }

    Set-HermesApiServerEnv
    $hermesPath = Get-Command hermes -ErrorAction SilentlyContinue
    if (-not $hermesPath) {
        Write-Warning "Hermes CLI was not found on PATH yet. Desktop was installed, but CLI verification was skipped."
    } else {
        & $hermesPath.Source --version | Write-Output
    }

    Write-Output "Hermes Desktop install verified: $($hermesExe.FullName)"
    Write-Output "Hermes API Server configuration seeded in ~/.hermes/.env and user environment."
}

function Set-WrightLlmConfig {
    param(
        [Parameter(Mandatory=$true)][string]$WrightDir,
        [Parameter(Mandatory=$true)][string]$LlmApiUrl
    )

    if (-not $LlmApiUrl.Trim()) {
        return
    }

    [Environment]::SetEnvironmentVariable("LLM_API_URL", $LlmApiUrl, "User")
    $env:LLM_API_URL = $LlmApiUrl

    $healthUrl = $LlmApiUrl.TrimEnd("/")
    if ($healthUrl.EndsWith("/v1")) {
        $healthUrl = $healthUrl.Substring(0, $healthUrl.Length - 3)
    }
    $healthUrl = "$($healthUrl.TrimEnd('/'))/health"
    [Environment]::SetEnvironmentVariable("LLM_HEALTH_URL", $healthUrl, "User")
    $env:LLM_HEALTH_URL = $healthUrl

    $dbPath = Join-Path $WrightDir "apps\api\state.db"
    $parent = Split-Path -Parent $dbPath
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    $py = @"
import sqlite3
db_path = r'''$dbPath'''
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
    $tmp = Join-Path $env:TEMP "wright-set-llm-config.py"
    Set-Content -Path $tmp -Value $py -Encoding UTF8
    python $tmp | Write-Output
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

function Enable-WrightPluginWithHermesCli {
    Write-Output "Enabling Wright plugin with Hermes CLI..."
    $hermesPath = Get-Command hermes -ErrorAction SilentlyContinue
    if (-not $hermesPath) {
        Write-Warning "Hermes CLI not found on PATH; YAML config was updated but CLI enable could not be run."
        return
    }

    & $hermesPath.Source plugins enable wright | Write-Output
    & $hermesPath.Source plugins list | Write-Output
}

function Test-WrightPluginInstall {
    param(
        [Parameter(Mandatory=$true)][string]$WrightDir
    )

    Write-Output "Verifying Wright plugin installation..."
    $activePlugin = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\plugins\wright"
    $commandsPath = Join-Path $activePlugin "commands.py"
    $bridgePath = Join-Path $activePlugin "bridge.py"
    $desktopConfigPath = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\config.yaml"

    if (-not (Test-Path $commandsPath)) {
        Write-Error "ERROR: Active Hermes Desktop plugin commands.py not found at $commandsPath"
        Exit 1
    }
    if (-not (Test-Path $bridgePath)) {
        Write-Error "ERROR: Active Hermes Desktop plugin bridge.py not found at $bridgePath"
        Exit 1
    }

    $commandsText = Get-Content -Path $commandsPath -Raw
    $bridgeText = Get-Content -Path $bridgePath -Raw
    if ($commandsText -notmatch "uvicorn") {
        Write-Error "ERROR: Active plugin commands.py does not contain uvicorn launcher."
        Exit 1
    }
    if ($commandsText -match "fastapi\s+run") {
        Write-Error "ERROR: Active plugin commands.py still contains fastapi run."
        Exit 1
    }
    if ($commandsText -notmatch "WRIGHT_REPO_DIR") {
        Write-Error "ERROR: Active plugin commands.py does not mention WRIGHT_REPO_DIR recovery guidance."
        Exit 1
    }
    if ($bridgeText -notmatch "apps.*api") {
        Write-Error "ERROR: Active plugin bridge.py does not include current apps/api repo detection."
        Exit 1
    }
    if ($env:WRIGHT_REPO_DIR -ne $WrightDir) {
        Write-Error "ERROR: WRIGHT_REPO_DIR is not set for the current session."
        Exit 1
    }
    if ($env:WRIGHT_API_HOST -ne "0.0.0.0") {
        Write-Error "ERROR: WRIGHT_API_HOST is not set to 0.0.0.0 for VM host-port testing."
        Exit 1
    }
    if ($env:WRIGHT_UI_MODE -ne "browser") {
        Write-Error "ERROR: WRIGHT_UI_MODE is not set to browser for Wright UI routing."
        Exit 1
    }
    if ($env:HERMES_API_BASE_URL -ne "http://127.0.0.1:8642") {
        Write-Error "ERROR: HERMES_API_BASE_URL is not set for Wright-to-Hermes connectivity."
        Exit 1
    }
    if (-not (Test-Path $desktopConfigPath)) {
        Write-Error "ERROR: Hermes Desktop agent config.yaml not found at $desktopConfigPath"
        Exit 1
    }
    $desktopConfigText = Get-Content -Path $desktopConfigPath -Raw
    if ($desktopConfigText -notmatch "wright") {
        Write-Error "ERROR: Hermes Desktop agent config.yaml does not enable the Wright plugin."
        Exit 1
    }
    $staleUserPlugin = Join-Path $env:USERPROFILE ".hermes\plugins\wright"
    if (Test-Path $staleUserPlugin) {
        Write-Error "ERROR: Stale duplicate user plugin copy still exists at $staleUserPlugin"
        Exit 1
    }
    $hermesPath = Get-Command hermes -ErrorAction SilentlyContinue
    if ($hermesPath) {
        $pluginList = & $hermesPath.Source plugins list 2>&1 | Out-String
        Write-Output $pluginList
        if ($pluginList -notmatch "wright") {
            Write-Error "ERROR: Hermes CLI does not list the Wright plugin."
            Exit 1
        }
        if ($pluginList -match "wright[\s\S]*not enabled") {
            Write-Error "ERROR: Hermes CLI still reports the Wright plugin as not enabled."
            Exit 1
        }
    }

    Write-Output "Wright plugin active path verified: $activePlugin"
}

function Save-HermesDesktopPath {
    param(
        [Parameter(Mandatory=$true)][string]$WrightDir
    )

    $hermesExe = Find-HermesDesktopExe
    if (-not $hermesExe) {
        Write-Warning "Could not locate Hermes.exe. Install Hermes Desktop manually, then rerun with -SkipDesktop."
        return $null
    }

    $pathDir = Join-Path $WrightDir "tmp"
    if (-not (Test-Path $pathDir)) { New-Item -ItemType Directory -Path $pathDir -Force | Out-Null }
    Set-Content -Path (Join-Path $pathDir "hermes-desktop-path.txt") -Value $hermesExe.FullName
    Write-Output "Found Hermes.exe at: $($hermesExe.FullName)"
    return $hermesExe.FullName
}

function Stop-WrightRuntimeProcesses {
    param(
        [Parameter(Mandatory=$true)][string]$WrightDir
    )

    Write-Output "Stopping any existing Wright backend and Hermes Desktop processes..."
    $pidPath = Join-Path $WrightDir "tmp\wright-api.pid"
    if (Test-Path $pidPath) {
        $pidText = (Get-Content -Path $pidPath -Raw).Trim()
        if ($pidText -match '^\d+$') {
            taskkill /PID $pidText /F 2>$null | Out-Null
        }
        Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
    }

    Get-Process -Name Hermes -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue

    foreach ($name in @("node", "npm", "uvicorn", "python")) {
        Get-Process -Name $name -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -like "$WrightDir*" } |
            Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

function Clear-WrightRuntimeState {
    param(
        [Parameter(Mandatory=$true)][string]$WrightDir
    )

    Write-Output "Clearing Wright runtime state for a clean install..."
    $patterns = @(
        (Join-Path $WrightDir "apps\api\state.db"),
        (Join-Path $WrightDir "apps\api\state.db-journal"),
        (Join-Path $WrightDir "apps\api\state.db-wal"),
        (Join-Path $WrightDir "apps\api\state.db-shm"),
        (Join-Path $WrightDir "apps\api\*.log"),
        (Join-Path $WrightDir "tmp\*.log"),
        (Join-Path $WrightDir "tmp\*.pid")
    )

    foreach ($pattern in $patterns) {
        Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName.StartsWith($WrightDir, [System.StringComparison]::OrdinalIgnoreCase) } |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-WithRetry {
    param(
        [Parameter(Mandatory=$true)][scriptblock]$ScriptBlock,
        [string]$Description = "command",
        [int]$Attempts = 3,
        [int]$DelaySeconds = 5
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        Write-Output "$Description (attempt $attempt/$Attempts)..."
        & $ScriptBlock
        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
            return
        }
        if ($attempt -lt $Attempts) {
            Write-Warning "$Description failed with exit code $LASTEXITCODE. Retrying after cleanup..."
            Stop-WrightRuntimeProcesses -WrightDir $WrightDir
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    Write-Error "ERROR: $Description failed after $Attempts attempts."
    Exit 1
}

function Start-HermesGateway {
    Write-Output "Starting Hermes gateway with API server enabled for Wright browser connectivity..."
    $hermesPath = Get-Command hermes -ErrorAction SilentlyContinue
    if (-not $hermesPath) {
        Write-Warning "Hermes CLI not found on PATH; Wright may show Hermes as disconnected."
        return
    }

    Set-HermesApiServerEnv

    $gatewayTaskName = "LaunchHermesGateway"
    Get-ScheduledTask -TaskName $gatewayTaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

    $argument = "/c `"set `"HERMES_ACCEPT_HOOKS=1`" && set `"API_SERVER_ENABLED=true`" && set `"API_SERVER_HOST=127.0.0.1`" && set `"API_SERVER_PORT=8642`" && set `"API_SERVER_KEY=wright-local-dev`" && `"$($hermesPath.Source)`" gateway`""
    $gatewayAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $argument
    $gatewayPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    Register-ScheduledTask -TaskName $gatewayTaskName -Action $gatewayAction -Principal $gatewayPrincipal | Out-Null
    Start-ScheduledTask -TaskName $gatewayTaskName
    Start-Sleep -Seconds 3
}

# ---- Step 1: Install System Tools -----------------------------------
if (-not $SkipTools) {
    Write-Output ""
    Write-Output "============================================"
    Write-Output "  Step 1: Installing System Tools"
    Write-Output "============================================"

    # Chocolatey
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        # Clean up broken/leftover install (directory exists but no choco.exe)
        $chocoDir = [System.Environment]::GetEnvironmentVariable("ChocolateyInstall","Machine")
        if (-not $chocoDir) { $chocoDir = "$env:ProgramData\chocolatey" }
        if ((Test-Path $chocoDir) -and -not (Test-Path (Join-Path $chocoDir "bin\choco.exe"))) {
            Write-Output "Removing broken Chocolatey install at $chocoDir..."
            Remove-Item $chocoDir -Recurse -Force -ErrorAction SilentlyContinue
        }

        Write-Output "Installing Chocolatey..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    } else {
        Write-Output "Chocolatey already installed."
    }
    Refresh-Path

    # Core tools
    Write-Output "Installing git, Node.js LTS, Python 3..."
    choco install git -y
    choco install nodejs-lts -y
    choco install python3 -y
    Refresh-Path

    # uv
    Write-Output "Installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    Refresh-Path

    Write-Output ""
    Write-Output "--- Installed Versions ---"
    git --version
    node --version
    python --version
    uv --version
    Write-Output "--------------------------"
    Write-Output ""
    Write-Output "[CHECKPOINT] Take a Hyper-V checkpoint named 'tools-ready' now."
    Write-Output ""
}

# ---- Step 2: Set Up Hermes Desktop (Official Installer) -------------
if (-not $SkipDesktop) {
    Write-Output ""
    Write-Output "============================================"
    Write-Output "  Step 2: Setting Up Hermes Desktop"
    Write-Output "============================================"
    Refresh-Path

    $setupUrl = $HermesSetupUrl
    $setupPath = "C:\Users\Public\Downloads\Hermes-Setup.exe"
    if (Test-Path $setupPath) {
        Remove-Item $setupPath -Force -ErrorAction SilentlyContinue
    }
    Write-Output "Downloading Hermes-Setup.exe from $setupUrl..."
    Invoke-WebRequest -Uri $setupUrl -OutFile $setupPath -UseBasicParsing
    
    Write-Output "Installing Hermes Desktop silently in interactive user session..."
    $installTaskName = "InstallHermesDesktop"
    Get-ScheduledTask -TaskName $installTaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    $installAction = New-ScheduledTaskAction -Execute $setupPath -Argument "/S"
    $installPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    Register-ScheduledTask -TaskName $installTaskName -Action $installAction -Principal $installPrincipal | Out-Null
    Start-ScheduledTask -TaskName $installTaskName

    Write-Output "Waiting for scheduled installer to finish..."
    for ($i = 0; $i -lt 90; $i++) {
        $task = Get-ScheduledTask -TaskName $installTaskName -ErrorAction SilentlyContinue
        $hermesExe = Find-HermesDesktopExe
        if ($hermesExe) { break }
        if ($task -and $task.State -eq "Ready" -and $i -gt 10) { break }
        Start-Sleep -Seconds 2
    }

    Write-Output "Locating installed Hermes.exe..."
    $hermesExe = $null
    for ($i = 0; $i -lt 30; $i++) {
        $hermesExe = Find-HermesDesktopExe
        if ($hermesExe) { break }
        Start-Sleep -Seconds 2
    }

    if (-not $hermesExe) {
        Write-Warning "Scheduled-task install did not produce Hermes.exe; retrying installer directly in this user context..."
        $directProc = Start-Process -FilePath $setupPath -ArgumentList "/S" -Wait -PassThru
        Write-Output "Direct installer exited with code $($directProc.ExitCode)."
        for ($i = 0; $i -lt 90; $i++) {
            $hermesExe = Find-HermesDesktopExe
            if ($hermesExe) { break }
            Start-Sleep -Seconds 2
        }
    }
    
    # Clean up the temporary installation scheduled task
    Get-ScheduledTask -TaskName $installTaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    if (-not $hermesExe) {
        Write-Error "ERROR: Could not find Hermes.exe after installation."
        Exit 1
    }
    $hermesExePath = $hermesExe.FullName
    Write-Output "Found Hermes.exe at: $hermesExePath"
    Test-HermesDesktopInstall

    # Save the discovered Hermes.exe path for Step 4
    $pathDir = Join-Path $WrightDir "tmp"
    if (-not (Test-Path $pathDir)) { New-Item -ItemType Directory -Path $pathDir -Force | Out-Null }
    Set-Content -Path (Join-Path $pathDir "hermes-desktop-path.txt") -Value $hermesExePath
} else {
    Write-Output "Skipping Hermes Desktop installer; checking for existing Hermes Desktop install..."
    Save-HermesDesktopPath -WrightDir $WrightDir | Out-Null
}

# ---- Step 3: Install Wright (User-Style) ----------------------------
if (-not $SkipWright) {
    Write-Output ""
    Write-Output "============================================"
    Write-Output "  Step 3: Installing Wright (User-Style)"
    Write-Output "============================================"
    Refresh-Path

    # 3a. Set up wright repo (extract local archive or clone)
    if (Test-Path "C:\Users\Public\Downloads\wright.zip") {
        Write-Output "Extracting local Wright repository archive..."
        if (-not (Test-Path $WrightDir)) {
            New-Item -ItemType Directory -Path $WrightDir | Out-Null
        }
        tar -xf "C:\Users\Public\Downloads\wright.zip" -C $WrightDir
        Clear-WrightRuntimeState -WrightDir $WrightDir
    } elseif (-not (Test-Path $WrightDir)) {
        Write-Output "Cloning wright repository..."
        git clone https://github.com/burhop/wright.git $WrightDir
        Clear-WrightRuntimeState -WrightDir $WrightDir
    } else {
        Write-Output "Wright repo already at $WrightDir, pulling latest..."
        Push-Location $WrightDir -ErrorAction Stop
        git pull
        Pop-Location
        Clear-WrightRuntimeState -WrightDir $WrightDir
    }

    # 3b. Install Hermes Agent + Wright Plugin via uv tool
    Write-Output "Installing hermes-agent with wright plugin..."
    uv tool install hermes-agent --with "$WrightDir\hermes-plugin-wright" --python 3.13 --force
    Refresh-Path

    # Verify hermes is on PATH
    Write-Output "Verifying hermes CLI..."
    hermes --version

    # 3c. Install wright Python dependencies
    Write-Output "Installing Wright Python dependencies..."
    Push-Location $WrightDir -ErrorAction Stop
    Stop-WrightRuntimeProcesses -WrightDir $WrightDir
    Invoke-WithRetry -Description "uv sync --all-packages --all-groups" -ScriptBlock {
        uv sync --all-packages --all-groups
    }

    # Configure Hermes Agent to enable Wright plugin and allow platform toolsets
    Write-Output "Configuring Hermes Agent to enable Wright plugin..."
    uv run python -c "
import os, yaml
paths = [
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'hermes', 'hermes-agent', 'config.yaml'),
    os.path.expanduser('~/.hermes/config.yaml'),
    os.path.expanduser('~/.hermes/profiles/wright/config.yaml')
]
for p in paths:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    cfg = {}
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
        except Exception:
            pass
    if 'plugins' not in cfg:
        cfg['plugins'] = {}
    pl = cfg['plugins']
    if 'enabled' not in pl:
        pl['enabled'] = []
    if isinstance(pl['enabled'], str):
        pl['enabled'] = [pl['enabled']]
    if 'wright' not in pl['enabled']:
        pl['enabled'].append('wright')
    if 'platform_toolsets' not in cfg:
        cfg['platform_toolsets'] = {}
    pt = cfg['platform_toolsets']
    if 'cli' not in pt:
        pt['cli'] = ['file', 'terminal', 'plugins', 'mcp']
    elif isinstance(pt['cli'], list):
        for t in ['file', 'terminal', 'plugins', 'mcp']:
            if t not in pt['cli']:
                pt['cli'].append(t)
    if 'mcp_servers' in cfg and 'wrightgateway' in cfg['mcp_servers']:
        wg = cfg['mcp_servers']['wrightgateway']
        if 'args' in wg and isinstance(wg['args'], list):
            wg['args'] = [a.replace('/home/burhop/repos/wright', r'C:\wright') for a in wg['args']]
    with open(p, 'w', encoding='utf-8') as f:
        yaml.safe_dump(cfg, f, default_flow_style=False)
"
    Pop-Location

    # 3d. Install wright Node dependencies and build frontend
    Write-Output "Installing Wright Node dependencies..."
    Push-Location $WrightDir -ErrorAction Stop
    Stop-WrightRuntimeProcesses -WrightDir $WrightDir
    Invoke-WithRetry -Description "npm install" -ScriptBlock {
        npm install
    }
    Pop-Location

    Write-Output "Building Wright frontend (production)..."
    Push-Location $WrightDir -ErrorAction Stop
    npm run build --workspace=apps/web
    Pop-Location

    # 3e. Build desktop assets
    Write-Output "Building Wright desktop assets..."
    Push-Location $WrightDir -ErrorAction Stop
    npm run build:desktop --workspace=apps/web
    Pop-Location

    # 3f. Register the Wright plugin in every Hermes Desktop load path we know about
    Install-WrightPluginForHermes -WrightDir $WrightDir
    Enable-WrightPluginWithHermesCli
    Test-WrightPluginInstall -WrightDir $WrightDir

    Write-Output ""
    Write-Output "Wright installed successfully."
    Write-Output ""
    Write-Output "[CHECKPOINT] Take a Hyper-V checkpoint named 'ready-to-run' now."
    Write-Output "  Future sessions start here instantly."
    Write-Output ""
}

# ---- Step 4: Start Everything ---------------------------------------
if ($StartServers) {
    Write-Output ""
    Write-Output "============================================"
    Write-Output "  Starting Wright + Hermes Desktop"
    Write-Output "============================================"
    Refresh-Path

    # As per user rules/instructions, we do not start the Wright backend directly.
    # The Wright plugin's '/wright start' command inside Hermes Desktop will start it.
    Write-Output "Skipping direct Wright backend startup (will be started via Hermes plugin)."

    Stop-WrightRuntimeProcesses -WrightDir $WrightDir
    Install-WrightPluginForHermes -WrightDir $WrightDir
    Enable-WrightPluginWithHermesCli
    Test-WrightPluginInstall -WrightDir $WrightDir
    Start-HermesGateway
 
    # Start Hermes Desktop in the active interactive session using a Scheduled Task (bypasses Session 0 isolation)
    Write-Output "Starting Hermes Desktop in interactive session..."
    $desktopTaskName = "LaunchHermesDesktop"
    Get-ScheduledTask -TaskName $desktopTaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    # Load discovered Hermes.exe path
    $hermesExePath = $null
    $pathFile = Join-Path $WrightDir "tmp\hermes-desktop-path.txt"
    if (Test-Path $pathFile) {
        $hermesExePath = (Get-Content -Path $pathFile -Raw).Trim()
    } else {
        # Fallback to search
        $hermesExe = Find-HermesDesktopExe
        if ($hermesExe) { $hermesExePath = $hermesExe.FullName }
    }
    
    if (-not $hermesExePath) {
        Write-Error "ERROR: Could not locate installed Hermes.exe. Run provisioning without -SkipDesktop first."
        Exit 1
    }
    
    $desktopAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"set `"WRIGHT_REPO_DIR=C:\wright`" && set `"WRIGHT_API_HOST=0.0.0.0`" && set `"WRIGHT_UI_MODE=browser`" && set `"HERMES_API_BASE_URL=http://127.0.0.1:8642`" && set `"HERMES_API_KEY=wright-local-dev`" && set `"API_SERVER_ENABLED=true`" && set `"API_SERVER_KEY=wright-local-dev`" && set `"LLM_API_URL=$LlmApiUrl`" && start `"`" `"$hermesExePath`"`""
    $desktopPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    Register-ScheduledTask -TaskName $desktopTaskName -Action $desktopAction -Principal $desktopPrincipal | Out-Null
    Start-ScheduledTask -TaskName $desktopTaskName
    
    # Wait a few seconds for launch, and keep tasks running in Task Scheduler
    Start-Sleep -Seconds 5
 
    Write-Output ""
    Write-Output "============================================"
    Write-Output "  Everything is running!"
    Write-Output "============================================"
    Write-Output ""
    Write-Output "  Wright API:        http://localhost:8000"
    Write-Output "  Wright UI:         http://localhost:8000  (served by FastAPI)"
    Write-Output "  Hermes Desktop:    (Electron window should appear in VM)"
    Write-Output ""
} elseif (-not $SkipWright -or -not $SkipDesktop) {
    Write-Output ""
    Write-Output "============================================"
    Write-Output "  Provisioning Complete!"
    Write-Output "============================================"
    Write-Output ""
    Write-Output "  To start everything:"
    Write-Output "    .\provision-vm.ps1 -SkipTools -SkipWright -SkipDesktop -StartServers"
    Write-Output ""
    Write-Output "  Or manually:"
    Write-Output "    cd $WrightDir"
    Write-Output "    uv run uvicorn api.main:app --host 0.0.0.0 --port 8000"
    Write-Output ""
    Write-Output "    Or launch the installed Hermes Desktop app from your Start Menu"
    Write-Output ""
}
