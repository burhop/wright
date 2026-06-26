param(
    [string]$VmName = "wright-hermes-manual",
    [switch]$Restart
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
        "-VmName", "`"$VmName`""
    )
    if ($Restart) {
        $arguments += "-Restart"
    }
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to disconnect the VM network."
    return
}

$vm = Get-VM -Name $VmName -ErrorAction Stop
$logRoot = if ($vm.Path) { $vm.Path } else { Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual") $VmName }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot "manual-vm-disable-network.log"

Start-Transcript -Path $logPath -Force
try {
    Disconnect-VMNetworkAdapter -VMName $VmName
    Write-Output "Disconnected VM network adapter."
    Write-Output "  VM: $VmName"

    if ($Restart) {
        Restart-VM -Name $VmName -Force
        Start-Process vmconnect.exe -ArgumentList "localhost `"$VmName`""
        Write-Output "Restarted VM and reopened VMConnect."
    }
} finally {
    Stop-Transcript
}
