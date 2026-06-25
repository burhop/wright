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
    [switch]$StartServers    # Start Wright + open Hermes Desktop
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

    $setupUrl = "https://hermes-assets.nousresearch.com/Hermes-Setup.exe?build=de281bcebc26"
    $setupPath = "C:\Users\Public\Downloads\Hermes-Setup.exe"
    if (-not (Test-Path $setupPath)) {
        Write-Output "Downloading Hermes-Setup.exe..."
        Invoke-WebRequest -Uri $setupUrl -OutFile $setupPath -UseBasicParsing
    }
    
    Write-Output "Installing Hermes Desktop silently in interactive user session..."
    $installTaskName = "InstallHermesDesktop"
    Get-ScheduledTask -TaskName $installTaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    $installAction = New-ScheduledTaskAction -Execute $setupPath -Argument "/S"
    $installPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    Register-ScheduledTask -TaskName $installTaskName -Action $installAction -Principal $installPrincipal | Out-Null
    Start-ScheduledTask -TaskName $installTaskName

    # Wait for the installer process or Hermes.exe to appear
    Write-Output "Waiting for installation to finish..."
    
    # Locate Hermes.exe dynamically
    Write-Output "Locating installed Hermes.exe..."
    $hermesExe = $null
    for ($i = 0; $i -lt 30; $i++) {
        $hermesExe = Get-ChildItem -Path "$env:LOCALAPPDATA\hermes", "$env:LOCALAPPDATA\Programs", "$env:ProgramFiles" -Filter "Hermes.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hermesExe) { break }
        Start-Sleep -Seconds 2
    }
    
    # Clean up the temporary installation scheduled task
    Get-ScheduledTask -TaskName $installTaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    
    if (-not $hermesExe) {
        Write-Error "ERROR: Could not find Hermes.exe after installation."
        Exit 1
    }
    $hermesExePath = $hermesExe.FullName
    Write-Output "Found Hermes.exe at: $hermesExePath"

    # Save the discovered Hermes.exe path for Step 4
    $pathDir = Join-Path $WrightDir "tmp"
    if (-not (Test-Path $pathDir)) { New-Item -ItemType Directory -Path $pathDir -Force | Out-Null }
    Set-Content -Path (Join-Path $pathDir "hermes-desktop-path.txt") -Value $hermesExePath
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
    } elseif (-not (Test-Path $WrightDir)) {
        Write-Output "Cloning wright repository..."
        git clone https://github.com/burhop/wright.git $WrightDir
    } else {
        Write-Output "Wright repo already at $WrightDir, pulling latest..."
        Push-Location $WrightDir -ErrorAction Stop
        git pull
        Pop-Location
    }

    # 3b. Install Hermes Agent + Wright Plugin via uv tool
    Write-Output "Installing hermes-agent with wright plugin..."
    uv tool install hermes-agent --with "$WrightDir\hermes-plugin-wright" --python 3.13
    Refresh-Path

    # Verify hermes is on PATH
    Write-Output "Verifying hermes CLI..."
    hermes --version

    # 3c. Install wright Python dependencies
    Write-Output "Installing Wright Python dependencies..."
    Push-Location $WrightDir -ErrorAction Stop
    uv sync --all-packages --no-dev

    # Configure Hermes Agent to enable Wright plugin and allow platform toolsets
    Write-Output "Configuring Hermes Agent to enable Wright plugin..."
    uv run python -c "
import os, yaml
paths = [
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
    npm install
    Pop-Location

    Write-Output "Building Wright frontend (production)..."
    Push-Location $WrightDir -ErrorAction Stop
    npm run build --workspace=apps/web
    Pop-Location

    # 3e. Build desktop assets
    Write-Output "Building Wright desktop assets..."
    Push-Location (Join-Path $WrightDir "apps/web") -ErrorAction Stop
    $env:BUILD_TARGET = "desktop"
    npx tsc -b
    npx vite build
    Remove-Item env:BUILD_TARGET -ErrorAction SilentlyContinue
    Pop-Location

    # 3f. Register the wright plugin by copying the files to the plugin directory
    $pluginsDir = Join-Path $env:USERPROFILE ".hermes\plugins"
    if (-not (Test-Path $pluginsDir)) {
        New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null
    }
    $pluginTarget = Join-Path $pluginsDir "wright"
    if (Test-Path $pluginTarget) {
        Remove-Item $pluginTarget -Force -Recurse -ErrorAction SilentlyContinue
    }
    Write-Output "Copying plugin files to $pluginTarget..."
    Copy-Item -Path "$WrightDir\hermes-plugin-wright" -Destination $pluginTarget -Recurse -Force | Out-Null

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
        $hermesExe = Get-ChildItem -Path "$env:LOCALAPPDATA\hermes", "$env:LOCALAPPDATA\Programs", "$env:ProgramFiles" -Filter "Hermes.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hermesExe) { $hermesExePath = $hermesExe.FullName }
    }
    
    if (-not $hermesExePath) {
        Write-Error "ERROR: Could not locate installed Hermes.exe. Run provisioning without -SkipDesktop first."
        Exit 1
    }
    
    $desktopAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"set WRIGHT_REPO_DIR=C:\wright && start `"`" `"$hermesExePath`"`""
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
