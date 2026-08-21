[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$runbook = "docs/contributing/dev-push-runbook.md"
$script = Join-Path $PSScriptRoot "check-dev-merge.sh"

Write-Host "Required reading: $runbook"

$gitCommand = Get-Command git.exe -ErrorAction Stop
$gitRoot = Split-Path -Parent (Split-Path -Parent $gitCommand.Source)
$candidates = @(
    (Join-Path $gitRoot "bin\bash.exe"),
    (Join-Path $env:ProgramFiles "Git\bin\bash.exe")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$gitBash = $candidates | Select-Object -First 1
if (-not $gitBash) {
    throw "Git Bash is required. Install Git for Windows or run scripts/check-dev-merge.sh from a Unix shell."
}

Push-Location $root
try {
    & $gitBash $script
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
