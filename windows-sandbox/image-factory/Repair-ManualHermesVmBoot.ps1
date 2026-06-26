param(
    [string]$VmName = "wright-hermes-manual",
    [string]$IsoPath = (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\image-factory\iso\Win11_25H2_English_x64.noprompt.iso")
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
        "-IsoPath", "`"$IsoPath`""
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to repair the VM boot media."
    return
}

if (-not (Test-Path $IsoPath)) {
    throw "ISO not found: $IsoPath"
}

$vm = Get-VM -Name $VmName -ErrorAction Stop
$logRoot = if ($vm.Path) { $vm.Path } else { Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual") $VmName }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot "manual-vm-boot-repair.log"

Start-Transcript -Path $logPath -Force
try {
    if ($vm.State -ne "Off") {
        Stop-VM -Name $VmName -Force
    }

    $dvd = Get-VMDvdDrive -VMName $VmName -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $dvd) {
        Add-VMDvdDrive -VMName $VmName -Path $IsoPath
    } else {
        Set-VMDvdDrive -VMName $VmName -ControllerNumber $dvd.ControllerNumber -ControllerLocation $dvd.ControllerLocation -Path $IsoPath
    }

    Set-VMFirmware -VMName $VmName -EnableSecureBoot Off
    $dvd = Get-VMDvdDrive -VMName $VmName | Select-Object -First 1
    Set-VMFirmware -VMName $VmName -FirstBootDevice $dvd

    Start-VM -Name $VmName
    Start-Process vmconnect.exe -ArgumentList "localhost `"$VmName`""

    Write-Output "Repaired manual VM boot media."
    Write-Output "  VM:  $VmName"
    Write-Output "  ISO: $IsoPath"
} finally {
    Stop-Transcript
}
