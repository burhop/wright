$ErrorActionPreference = "Stop"
$log = "D:\repos\wright\windows-sandbox\restore-hermes-installed.latest.log"
function Log($m) { $line = "$(Get-Date -Format o) $m"; $line | Tee-Object -FilePath $log -Append }
try {
  if (Test-Path $log) { Remove-Item $log -Force }
  Log "Starting restore to hermes-installed"
  $vm = Get-VM -Name "Wright-Hermes-Sandbox" -ErrorAction Stop
  Log "Initial VM state: $($vm.State)"
  if ($vm.State -ne "Off") { Log "Stopping VM"; Stop-VM -Name "Wright-Hermes-Sandbox" -Force -ErrorAction Stop; Log "Stopped VM" }
  $snap = Get-VMSnapshot -VMName "Wright-Hermes-Sandbox" -Name "hermes-installed" -ErrorAction Stop
  Log "Restoring snapshot: $($snap.Name) $($snap.CreationTime)"
  Restore-VMSnapshot -VMName "Wright-Hermes-Sandbox" -Name "hermes-installed" -Confirm:$false -ErrorAction Stop
  Log "Restore completed"
  Start-VM -Name "Wright-Hermes-Sandbox" -ErrorAction Stop
  Log "Started VM"
  $vm = Get-VM -Name "Wright-Hermes-Sandbox" -ErrorAction Stop
  Log "Final VM state: $($vm.State)"
} catch {
  Log "ERROR: $($_.Exception.Message)"
  Log ($_.ScriptStackTrace | Out-String)
  exit 1
}
