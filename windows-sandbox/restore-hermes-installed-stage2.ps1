$ErrorActionPreference = "Stop"
$log = "D:\repos\wright\windows-sandbox\restore-hermes-installed.latest.log"
function Log($m) { $line = "$(Get-Date -Format o) $m"; $line | Tee-Object -FilePath $log -Append }
try {
  Log "Starting restore while VM is expected Off"
  $vm = Get-VM -Name "Wright-Hermes-Sandbox" -ErrorAction Stop
  Log "VM state before restore: $($vm.State)"
  if ($vm.State -ne "Off") { throw "VM must be Off before restore, got $($vm.State)" }
  Restore-VMSnapshot -VMName "Wright-Hermes-Sandbox" -Name "hermes-installed" -Confirm:$false -ErrorAction Stop
  Log "Restore completed"
  Start-VM -Name "Wright-Hermes-Sandbox" -ErrorAction Stop
  Log "Started VM"
  $vm = Get-VM -Name "Wright-Hermes-Sandbox" -ErrorAction Stop
  Log "VM state after start: $($vm.State)"
} catch {
  Log "ERROR: $($_.Exception.Message)"
  Log ($_.ScriptStackTrace | Out-String)
  exit 1
}
