param(
    [string]$VmName = "wright-hermes-manual",
    [int]$StartupMemoryGb = 4,
    [int]$MinimumMemoryGb = 1,
    [int]$MaximumMemoryGb = 6
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdministrator)) {
    $arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`"",
        "-VmName", "`"$VmName`"",
        "-StartupMemoryGb", $StartupMemoryGb,
        "-MinimumMemoryGb", $MinimumMemoryGb,
        "-MaximumMemoryGb", $MaximumMemoryGb
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to start the VM."
    return
}

$vm = Get-VM -Name $VmName -ErrorAction Stop
$vmPath = $vm.Path
if (-not $vmPath) {
    $vmPath = Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual") $VmName
}
New-Item -ItemType Directory -Path $vmPath -Force | Out-Null
$logPath = Join-Path $vmPath "manual-vm-start.log"
Start-Transcript -Path $logPath -Force
try {
if ($vm.State -ne "Off") {
    Write-Output "VM '$VmName' is already $($vm.State). Opening VMConnect."
    Start-Process vmconnect.exe -ArgumentList "localhost `"$VmName`""
    return
}

Set-VMMemory -VMName $VmName `
    -DynamicMemoryEnabled $true `
    -MinimumBytes ([int64]$MinimumMemoryGb * 1GB) `
    -StartupBytes ([int64]$StartupMemoryGb * 1GB) `
    -MaximumBytes ([int64]$MaximumMemoryGb * 1GB)

Start-VM -Name $VmName
Start-Process vmconnect.exe -ArgumentList "localhost `"$VmName`""
Write-Output "Started VM '$VmName' with ${StartupMemoryGb}GB startup memory."
} finally {
    Stop-Transcript
}
