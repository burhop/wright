# One-time bootstrap for the Hyper-V Windows base VM.
#
# This creates or reuses the VM, opens VMConnect, waits for PowerShell Direct to
# work with the supplied guest credentials, and saves a "base-ready" checkpoint.
# It does not install developer tools, Hermes Desktop, or Wright.

param(
    [string]$VmName = "Wright-Hermes-Automation-Test",
    [string]$ImagePath = (Join-Path $PSScriptRoot ".vm\WinDev2407Eval.vhdx"),
    [switch]$SkipDownload,
    [string]$GuestUsername = "User",
    [string]$GuestPassword = "password",
    [switch]$AllowCredentialPrompt
)

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    $argList = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $PSCommandPath,
        "-VmName", $VmName,
        "-ImagePath", $ImagePath,
        "-GuestUsername", $GuestUsername,
        "-GuestPassword", $GuestPassword
    )
    if ($SkipDownload) { $argList += "-SkipDownload" }
    if ($AllowCredentialPrompt) { $argList += "-AllowCredentialPrompt" }
    Start-Process -FilePath powershell.exe -ArgumentList $argList -Verb RunAs
    Write-Output "Relaunched elevated bootstrap window for VM '$VmName'."
    Exit 0
}

Write-Output "============================================"
Write-Output "  Wright Base VM Bootstrap"
Write-Output "============================================"
Write-Output "VM:          $VmName"
Write-Output "Guest user:  $GuestUsername"
Write-Output ""
Write-Output "If VMConnect opens to Windows setup or a login screen, complete it using"
Write-Output "the same guest credentials passed to this script. The script will continue"
Write-Output "polling PowerShell Direct and save checkpoint 'base-ready' once it works."
Write-Output ""
Write-Output "If Windows reaches the desktop but this script keeps reporting"
Write-Output "'A remote session might have ended', open an elevated PowerShell inside"
Write-Output "the VM and run:"
Write-Output "  net user $GuestUsername $GuestPassword"
Write-Output "  Restart-Service -Name vmicvmsession -Force"
Write-Output ""

$runParams = @{
    VmName = $VmName
    ImagePath = $ImagePath
    UseExistingVm = $true
    BaseOnly = $true
    GuestUsername = $GuestUsername
    GuestPassword = $GuestPassword
}
if ($SkipDownload) { $runParams.SkipDownload = $true }
if ($AllowCredentialPrompt) { $runParams.AllowCredentialPrompt = $true }

& (Join-Path $PSScriptRoot "run-vm-test.ps1") @runParams
