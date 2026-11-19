[CmdletBinding()]
param([string]$Python = "python")

$ErrorActionPreference = "Stop"
& $Python (Join-Path $PSScriptRoot "../.github/test_distribution.py") --check-dev-push
exit $LASTEXITCODE
