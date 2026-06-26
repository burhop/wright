param(
    [string]$VmName = "wright-hermes-manual",
    [string]$SnapshotName = "wright-installed-verified"
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
        "-SnapshotName", "`"$SnapshotName`""
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to restore and start the VM checkpoint."
    return
}

$vm = Get-VM -Name $VmName -ErrorAction Stop
$snapshot = Get-VMSnapshot -VMName $VmName -Name $SnapshotName -ErrorAction Stop
$logRoot = if ($vm.Path) { $vm.Path } else { Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual") $VmName }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot "manual-vm-start-checkpoint.log"

Start-Transcript -Path $logPath -Force
try {
    $vm = Get-VM -Name $VmName -ErrorAction Stop
    for ($i = 1; $i -le 12 -and $vm.State -in @("Starting", "Stopping", "Saving", "Restoring"); $i++) {
        Write-Output "Waiting for VM transition state $($vm.State) ($i/12)..."
        Start-Sleep -Seconds 5
        $vm = Get-VM -Name $VmName -ErrorAction Stop
    }

    if ($vm.State -eq "Saved") {
        Remove-VMSavedState -VMName $VmName
    } elseif ($vm.State -ne "Off") {
        Stop-VM -Name $VmName -TurnOff -Force
    }

    Restore-VMSnapshot -VMName $VmName -Name $SnapshotName -Confirm:$false
    Start-VM -Name $VmName
    Start-Process vmconnect.exe -ArgumentList "localhost `"$VmName`""

    Write-Output "Restored and started VM checkpoint."
    Write-Output "  VM:         $VmName"
    Write-Output "  Checkpoint: $($snapshot.Name)"
} finally {
    Stop-Transcript
}
