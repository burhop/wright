param(
    [string]$VmName = "wright-hermes-manual",
    [string]$SnapshotName = "windows-installed-pre-hermes"
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
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to checkpoint the VM."
    return
}

$vm = Get-VM -Name $VmName -ErrorAction Stop
$logRoot = if ($vm.Path) { $vm.Path } else { Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual") $VmName }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot "manual-vm-checkpoint.log"

Start-Transcript -Path $logPath -Force
try {
    $existing = Get-VMSnapshot -VMName $VmName -Name $SnapshotName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Output "Checkpoint already exists."
        Write-Output "  VM:         $VmName"
        Write-Output "  Checkpoint: $SnapshotName"
        return
    }

    Set-VM -Name $VmName -CheckpointType Standard
    Checkpoint-VM -Name $VmName -SnapshotName $SnapshotName | Out-Null

    Write-Output "Checkpoint created."
    Write-Output "  VM:         $VmName"
    Write-Output "  Checkpoint: $SnapshotName"
} finally {
    Stop-Transcript
}
