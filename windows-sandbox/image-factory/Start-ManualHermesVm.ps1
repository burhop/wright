param(
    [string]$VmBaseName = "wright-hermes-manual",
    [string]$IsoPath = (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\image-factory\iso\Win11_25H2_English_x64.iso"),
    [string]$SwitchName = "Default Switch",
    [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual"),
    [int]$DiskSizeGb = 64
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
        "-VmBaseName", "`"$VmBaseName`"",
        "-IsoPath", "`"$IsoPath`"",
        "-SwitchName", "`"$SwitchName`"",
        "-OutputRoot", "`"$OutputRoot`"",
        "-DiskSizeGb", $DiskSizeGb
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to create and open the VM."
    return
}

if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
    throw "Hyper-V PowerShell cmdlets are not available."
}
if (-not (Test-Path $IsoPath)) {
    throw "Windows ISO not found: $IsoPath"
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$vmName = $VmBaseName
$index = 2
while (Get-VM -Name $vmName -ErrorAction SilentlyContinue) {
    $vmName = "$VmBaseName-$index"
    $index++
}

$vmPath = Join-Path $OutputRoot $vmName
New-Item -ItemType Directory -Path $vmPath -Force | Out-Null

$logPath = Join-Path $vmPath "manual-vm-create.log"
Start-Transcript -Path $logPath -Force
try {
    $vhdPath = Join-Path $vmPath "$vmName.vhdx"

    if (Test-Path $vhdPath) {
        throw "VHD already exists: $vhdPath"
    }

    $diskSizeBytes = [int64]$DiskSizeGb * 1GB
    New-VHD -Path $vhdPath -SizeBytes $diskSizeBytes -Dynamic | Out-Null
    New-VM -Name $vmName -Generation 2 -MemoryStartupBytes 6GB -VHDPath $vhdPath -Path $vmPath -SwitchName $SwitchName | Out-Null
    Set-VM -Name $vmName -ProcessorCount 4
    Set-VMMemory -VMName $vmName -DynamicMemoryEnabled $true -MinimumBytes 2GB -StartupBytes 6GB -MaximumBytes 8GB
    Set-VMFirmware -VMName $vmName -EnableSecureBoot Off
    Set-VMKeyProtector -VMName $vmName -NewLocalKeyProtector
    Enable-VMTPM -VMName $vmName
    Add-VMDvdDrive -VMName $vmName -Path $IsoPath

    $dvd = Get-VMDvdDrive -VMName $vmName
    Set-VMFirmware -VMName $vmName -FirstBootDevice $dvd
    Enable-VMIntegrationService -VMName $vmName -Name "Guest Service Interface" -ErrorAction SilentlyContinue

    Start-VM -Name $vmName
    Start-Process vmconnect.exe -ArgumentList "localhost `"$vmName`""

    Write-Output ""
    Write-Output "Manual Hermes VM is running."
    Write-Output "  VM:  $vmName"
    Write-Output "  VHD: $vhdPath"
    Write-Output "  ISO: $IsoPath"
    Write-Output ""
    Write-Output "When Windows Setup asks where to install, choose the unallocated virtual disk."
} finally {
    Stop-Transcript
}
