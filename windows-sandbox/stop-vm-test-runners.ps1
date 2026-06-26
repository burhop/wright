# Stop duplicate host-side VM provisioning runners.
#
# This is intentionally narrow: it only targets PowerShell processes whose
# command line includes run-vm-test.ps1 or the shared VM test log path.

$ErrorActionPreference = "Stop"

$currentPid = $PID
$targets = Get-CimInstance Win32_Process |
    Where-Object {
        $_.ProcessId -ne $currentPid -and
        $_.Name -match 'powershell' -and
        $_.CommandLine -and
        (
            $_.CommandLine -match 'run-vm-test\.ps1' -or
            $_.CommandLine -match 'run-vm-test\.latest\.log'
        )
    }

if (-not $targets) {
    Write-Output "No duplicate VM test runners found."
    Exit 0
}

foreach ($target in $targets) {
    Write-Output "Stopping process $($target.ProcessId): $($target.CommandLine)"
    Stop-Process -Id $target.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Output "Stopped $($targets.Count) VM test runner process(es)."
