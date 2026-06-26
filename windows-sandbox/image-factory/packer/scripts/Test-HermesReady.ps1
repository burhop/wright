$ErrorActionPreference = "Stop"

$metadataPath = "C:\wright-image-metadata.json"
if (-not (Test-Path $metadataPath)) {
    throw "Image metadata was not found at $metadataPath."
}

$metadata = Get-Content -Path $metadataPath -Raw | ConvertFrom-Json
if (-not (Test-Path $metadata.hermes_exe)) {
    throw "Hermes executable recorded in metadata does not exist: $($metadata.hermes_exe)"
}

$envPath = Join-Path $env:USERPROFILE ".hermes\.env"
if (-not (Test-Path $envPath)) {
    throw "Hermes .env was not found at $envPath."
}

$envText = Get-Content -Path $envPath -Raw
foreach ($expected in @(
    "API_SERVER_ENABLED=true",
    "API_SERVER_HOST=127.0.0.1",
    "API_SERVER_PORT=8642",
    "API_SERVER_KEY=wright-local-dev"
)) {
    if ($envText -notmatch [regex]::Escape($expected)) {
        throw "Hermes API setting missing: $expected"
    }
}

Write-Output "Hermes-ready image validation passed."
