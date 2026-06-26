# Hyper-V VM control helper for Wright + Hermes Desktop testing.
#
# Run from an Administrator PowerShell on the Windows host.
# Examples:
#   .\manage-vm.ps1 status
#   .\manage-vm.ps1 connect
#   .\manage-vm.ps1 stop
#   .\manage-vm.ps1 restart
#   .\manage-vm.ps1 expose
#   .\manage-vm.ps1 clear-expose

param(
    [Parameter(Position=0)]
    [ValidateSet("status", "start", "stop", "restart", "connect", "expose", "clear-expose")]
    [string]$Action = "status",

    [string]$VmName = "Wright-Hermes-Sandbox",
    [string]$ListenAddress = "127.0.0.1",
    [int]$HostPort = 18000,
    [int]$GuestPort = 8000
)

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "ERROR: Run this script from an Administrator PowerShell on the host."
    Exit 1
}

if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: Hyper-V PowerShell cmdlets are not available."
    Exit 1
}

$vm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
if (-not $vm) {
    Write-Error "ERROR: VM '$VmName' was not found."
    Exit 1
}

function Show-WrightVmStatus {
    param([string]$VmName)

    $vm = Get-VM -Name $VmName
    $snapshots = Get-VMSnapshot -VMName $VmName -ErrorAction SilentlyContinue | Sort-Object CreationTime
    $connections = Get-Process vmconnect -ErrorAction SilentlyContinue

    Write-Output ""
    Write-Output "VM:          $($vm.Name)"
    Write-Output "State:       $($vm.State)"
    Write-Output "CPU Usage:   $($vm.CPUUsage)%"
    Write-Output "Memory:      $([math]::Round($vm.MemoryAssigned / 1MB)) MB"
    Write-Output ""
    Write-Output "Checkpoints:"
    if ($snapshots) {
        foreach ($snapshot in $snapshots) {
            Write-Output "  - $($snapshot.Name)  $($snapshot.CreationTime)"
        }
    } else {
        Write-Output "  (none)"
    }
    Write-Output ""
    Write-Output "VM console windows open: $($connections.Count)"
    Write-Output ""
}

function Get-WrightVmIpv4Address {
    param([string]$VmName)

    $addresses = Get-VMNetworkAdapter -VMName $VmName |
        Select-Object -ExpandProperty IPAddresses -ErrorAction SilentlyContinue

    $ipv4 = $addresses |
        Where-Object {
            $_ -match '^\d{1,3}(\.\d{1,3}){3}$' -and
            $_ -notlike '169.254.*' -and
            $_ -ne '127.0.0.1'
        } |
        Select-Object -First 1

    if (-not $ipv4) {
        Write-Error "ERROR: Could not determine an IPv4 address for VM '$VmName'. Make sure it is running and logged in."
        Exit 1
    }

    return $ipv4
}

function Set-WrightVmPortForward {
    param(
        [string]$VmName,
        [string]$ListenAddress,
        [int]$HostPort,
        [int]$GuestPort
    )

    if ((Get-VM -Name $VmName).State -ne "Running") {
        Start-VM -Name $VmName
        Write-Output "Started VM '$VmName'. Waiting briefly for networking..."
        Start-Sleep -Seconds 5
    }

    $guestIp = Get-WrightVmIpv4Address -VmName $VmName
    Write-Output "Forwarding http://${ListenAddress}:${HostPort} -> http://${guestIp}:${GuestPort}"

    & netsh interface portproxy set v4tov4 `
        listenaddress=$ListenAddress listenport=$HostPort `
        connectaddress=$guestIp connectport=$GuestPort | Out-Null

    $ruleName = "Wright VM $VmName port $HostPort"
    if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalAddress $ListenAddress `
            -LocalPort $HostPort | Out-Null
    }

    Write-Output "Host endpoint ready: http://${ListenAddress}:${HostPort}"
}

function Clear-WrightVmPortForward {
    param(
        [string]$VmName,
        [string]$ListenAddress,
        [int]$HostPort
    )

    & netsh interface portproxy delete v4tov4 `
        listenaddress=$ListenAddress listenport=$HostPort | Out-Null

    $ruleName = "Wright VM $VmName port $HostPort"
    Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule

    Write-Output "Removed host forwarding for ${ListenAddress}:${HostPort}."
}

switch ($Action) {
    "status" {
        Show-WrightVmStatus -VmName $VmName
    }
    "start" {
        if ($vm.State -ne "Running") {
            Start-VM -Name $VmName
            Write-Output "Started VM '$VmName'."
        } else {
            Write-Output "VM '$VmName' is already running."
        }
        Show-WrightVmStatus -VmName $VmName
    }
    "stop" {
        if ($vm.State -ne "Off") {
            Stop-VM -Name $VmName -Force
            Write-Output "Stopped VM '$VmName'."
        } else {
            Write-Output "VM '$VmName' is already stopped."
        }
        Show-WrightVmStatus -VmName $VmName
    }
    "restart" {
        if ($vm.State -eq "Running") {
            Restart-VM -Name $VmName -Force
        } else {
            Start-VM -Name $VmName
        }
        Write-Output "Restarted VM '$VmName'."
        Show-WrightVmStatus -VmName $VmName
    }
    "connect" {
        if ($vm.State -ne "Running") {
            Start-VM -Name $VmName
            Write-Output "Started VM '$VmName'."
        }
        Start-Process vmconnect.exe -ArgumentList "localhost", $VmName -ErrorAction SilentlyContinue
        Write-Output "Opened a console window for VM '$VmName'."
        Show-WrightVmStatus -VmName $VmName
    }
    "expose" {
        Set-WrightVmPortForward -VmName $VmName -ListenAddress $ListenAddress -HostPort $HostPort -GuestPort $GuestPort
        Show-WrightVmStatus -VmName $VmName
    }
    "clear-expose" {
        Clear-WrightVmPortForward -VmName $VmName -ListenAddress $ListenAddress -HostPort $HostPort
    }
}
