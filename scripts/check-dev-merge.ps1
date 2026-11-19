[CmdletBinding()]
param([string]$Python = "python")

& (Join-Path $PSScriptRoot "check-dev-push.ps1") -Python $Python
exit $LASTEXITCODE
