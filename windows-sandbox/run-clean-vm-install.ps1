# Restore the Wright VM and reinstall Wright from the current repository archive,
# using a unique log file for this run.

param(
    [string]$GuestUsername = "User",
    [string]$GuestPassword = "password",
    [switch]$HermesAlreadyInstalled,
    [string]$LlmApiUrl = "http://192.168.1.165:8000/v1",
    [string]$HermesSetupUrl = "https://hermes-assets.nousresearch.com/Hermes-Setup.exe"
)

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Output "Restarting this script as Administrator..."
    $elevatedArgs = @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "`"$PSCommandPath`"",
        "-GuestUsername",
        "`"$GuestUsername`"",
        "-GuestPassword",
        "`"$GuestPassword`"",
        "-LlmApiUrl",
        "`"$LlmApiUrl`"",
        "-HermesSetupUrl",
        "`"$HermesSetupUrl`""
    )
    if ($HermesAlreadyInstalled) {
        $elevatedArgs += "-HermesAlreadyInstalled"
    }
    Start-Process powershell.exe -Verb RunAs -ArgumentList $elevatedArgs
    Exit 0
}

Set-Location $PSScriptRoot

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logPath = Join-Path $PSScriptRoot "run-vm-test.$stamp.log"

Write-Output "Writing clean VM install log to: $logPath"
$runArgs = @{
    SkipDownload = $true
    NoConnect = $true
    GuestUsername = $GuestUsername
    GuestPassword = $GuestPassword
    LlmApiUrl = $LlmApiUrl
    HermesSetupUrl = $HermesSetupUrl
}
if ($HermesAlreadyInstalled) {
    $runArgs.HermesAlreadyInstalled = $true
}

& .\run-vm-test.ps1 @runArgs 2>&1 | Tee-Object -FilePath $logPath

Write-Output "Clean VM install finished. Log: $logPath"
