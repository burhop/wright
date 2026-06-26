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

$metadataPath = "C:\wright-image-metadata.json"
if (-not (Test-Path $metadataPath)) {
    throw "Hermes-ready image metadata missing."
}

$metadata = Get-Content -Path $metadataPath -Raw | ConvertFrom-Json
if (-not (Test-Path $metadata.hermes_exe)) {
    throw "Hermes executable from image metadata is missing: $($metadata.hermes_exe)"
}

$activePlugin = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\plugins\wright"
Assert-FileContains -Path (Join-Path $activePlugin "commands.py") -Pattern "uvicorn" -Description "Active Wright plugin commands.py"
Assert-FileContains -Path (Join-Path $activePlugin "bridge.py") -Pattern "apps.*api" -Description "Active Wright plugin bridge.py"

$desktopConfigPath = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\config.yaml"
Assert-FileContains -Path $desktopConfigPath -Pattern "wright" -Description "Hermes Desktop agent config.yaml"

$envPath = Join-Path $env:USERPROFILE ".hermes\.env"
Assert-FileContains -Path $envPath -Pattern "API_SERVER_ENABLED=true" -Description "Hermes API environment"
Assert-FileContains -Path $envPath -Pattern "API_SERVER_PORT=8642" -Description "Hermes API environment"

Push-Location $WrightDir
try {
    uv run pytest
    npm run test --workspace=apps/web
} finally {
    Pop-Location
}

Write-Output "Wright + Hermes guest verification passed."
