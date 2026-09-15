# Reload only a dashboard whose saved launch and live listener are verified.
$ErrorActionPreference = 'Stop'
$dashboardRepo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$dashboardReceiptFile = Join-Path $dashboardRepo '.local-run/feature-081-live/dataset-dashboard.session.json'
# Preserve ISO offsets; ConvertFrom-Json may convert ISO strings to DateTime.
$dashboardJson = [System.Text.Json.JsonDocument]::Parse((Get-Content -LiteralPath $dashboardReceiptFile -Raw))
$dashboardSaved = $dashboardJson.RootElement
$dashboardPid = $dashboardSaved.GetProperty('pid').GetInt32()
$dashboardStarted = [DateTimeOffset]::Parse($dashboardSaved.GetProperty('started_at').GetString())
$dashboardParent = Get-CimInstance Win32_Process -Filter "ProcessId = $dashboardPid"
if ($null -eq $dashboardParent -or $dashboardParent.CommandLine -notmatch 'scripts/engineering_dataset_campaign.py.+serve.+--port.+8771') {
    throw 'Saved dashboard launcher is unavailable or changed; reconcile before restarting.'
}
$dashboardCreated = [DateTimeOffset]::Parse($dashboardParent.CreationDate.ToString('o'))
if ([Math]::Abs(($dashboardStarted-$dashboardCreated).TotalSeconds) -gt 25) { throw 'Dashboard launch timestamp mismatch.' }
$dashboardChildren = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $dashboardPid")
$dashboardListener = Get-NetTCPConnection -LocalPort 8771 -State Listen
$dashboardOwned = @($dashboardChildren | Where-Object { $_.ProcessId -eq $dashboardListener.OwningProcess -and $_.CommandLine -match 'scripts/engineering_dataset_campaign.py.+serve.+--port.+8771' })
if ($dashboardOwned.Count -ne 1) { throw 'Dashboard listener ownership is ambiguous.' }
$dashboardProof = @($dashboardParent, $dashboardOwned[0]) | Select-Object ProcessId,ParentProcessId,CreationDate,ExecutablePath
foreach ($dashboardProcess in @($dashboardOwned[0], $dashboardParent)) {
    $dashboardCurrent = Get-CimInstance Win32_Process -Filter "ProcessId = $($dashboardProcess.ProcessId)"
    if ($null -eq $dashboardCurrent) { continue }
    if ($dashboardCurrent.CreationDate -ne $dashboardProcess.CreationDate -or $dashboardCurrent.ExecutablePath -ne $dashboardProcess.ExecutablePath) {
        throw 'Dashboard PID changed before cleanup.'
    }
    Stop-Process -Id $dashboardProcess.ProcessId
}
$dashboardJson.Dispose()
$dashboardProof | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dashboardRepo '.local-run/feature-081-live/dataset-dashboard.previous-processes.json') -Encoding utf8
& (Join-Path $PSScriptRoot 'start-engineering-dataset-dashboard.ps1')
