param(
    [string]$WrightDir = "C:\wright"
)

$ErrorActionPreference = "Stop"

function Assert-FileContains {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Pattern,
        [Parameter(Mandatory=$true)][string]$Description
    )

    if (-not (Test-Path $Path)) {
        throw "$Description was not found at $Path."
    }
    $text = Get-Content -Path $Path -Raw
    if ($text -notmatch $Pattern) {
        throw "$Description did not contain expected pattern: $Pattern"
    }
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

$hermesExe = Find-HermesDesktopExe
if (-not $hermesExe) {
    throw "Hermes Desktop executable was not found."
}
Write-Output "Hermes Desktop: $hermesExe"

$hermesPython = Find-HermesAgentPython
if (-not $hermesPython) {
    throw "Hermes agent Python was not found."
}
Write-Output "Hermes agent Python: $hermesPython"

$activePlugin = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\plugins\wright"
Assert-FileContains -Path (Join-Path $activePlugin "commands.py") -Pattern "uvicorn" -Description "Active Wright plugin commands.py"
Assert-FileContains -Path (Join-Path $activePlugin "bridge.py") -Pattern "apps.*api" -Description "Active Wright plugin bridge.py"

$profilePlugin = Join-Path $env:USERPROFILE ".hermes\hermes-agent\plugins\wright"
Assert-FileContains -Path (Join-Path $profilePlugin "plugin.yaml") -Pattern "wright" -Description "Profile Wright plugin metadata"

$envPath = Join-Path $env:USERPROFILE ".hermes\.env"
Assert-FileContains -Path $envPath -Pattern "API_SERVER_ENABLED=true" -Description "Hermes API environment"
Assert-FileContains -Path $envPath -Pattern "API_SERVER_PORT=8642" -Description "Hermes API environment"

$importCheckPath = Join-Path $env:TEMP "wright-plugin-import-check.py"
$importCheck = @"
import importlib.util
import pathlib
import sys
plugin_dir = pathlib.Path(r"$activePlugin")
spec = importlib.util.spec_from_file_location(
    "wright",
    plugin_dir / "__init__.py",
    submodule_search_locations=[str(plugin_dir)],
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
print("Wright plugin import OK")
"@
Set-Content -Path $importCheckPath -Value $importCheck -Encoding UTF8
Invoke-Native $hermesPython $importCheckPath

$hermes = Get-Command hermes -ErrorAction SilentlyContinue
if ($hermes) {
    $pluginList = & $hermes.Source plugins list 2>&1 | Out-String
    Write-Output $pluginList
    if ($pluginList -notmatch "wright") {
        throw "Hermes CLI does not list the Wright plugin."
    }
} else {
    Write-Warning "Hermes CLI was not found on PATH; verified Hermes Desktop executable and plugin files instead."
}

Push-Location $WrightDir
try {
    Invoke-Native uv run pytest --import-mode=importlib
    Invoke-Native npm run test --workspace=apps/web
} finally {
    Pop-Location
}

Write-Output "Manual Wright + Hermes guest verification passed."
