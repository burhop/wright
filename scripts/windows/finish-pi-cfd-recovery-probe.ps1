param([Parameter(Mandatory)][string]$ReceiptPath)
$ErrorActionPreference = 'Stop'
$receiptFile = (Resolve-Path -LiteralPath $ReceiptPath).Path
$probe = Get-Content -LiteralPath $receiptFile -Raw | ConvertFrom-Json
$probeDirectory = (Resolve-Path -LiteralPath $probe.diagnostic_root).Path
$receiptStem = [IO.Path]::GetFileNameWithoutExtension($receiptFile)
$resultPath = Join-Path $probeDirectory "$receiptStem-terminal.json"
if (Test-Path -LiteralPath $resultPath) { Get-Content -LiteralPath $resultPath; return }
if ($probe.ownership -ne 'owned' -or $probe.container_id -notmatch '^[a-f0-9]{64}$') { throw 'No exact owned container receipt.' }
$inspection = & docker inspect $probe.container_id | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $inspection.Count -ne 1) { throw 'Container outcome unavailable; preserve unresolved receipt.' }
$actual = $inspection[0]
if ($actual.Id -ne $probe.container_id -or $actual.Image -ne $probe.image -or
    $actual.Config.Labels.'wright.purpose' -ne 'engineering-cfd-recovery' -or
    $actual.Name -ne "/$($probe.name)") { throw 'Exact container ownership verification failed.' }
if ($actual.State.Running) { [pscustomobject]@{state='running';container_id=$actual.Id} | ConvertTo-Json; return }
$logPath = Join-Path $probeDirectory "$receiptStem.log"
& docker logs $probe.container_id 2>&1 | Out-File -LiteralPath $logPath -Encoding utf8
$terminal = [ordered]@{
    container_id=$actual.Id; name=$probe.name; image=$actual.Image;
    state=$actual.State.Status; exit_code=$actual.State.ExitCode; oom_killed=$actual.State.OOMKilled;
    started_at=$actual.State.StartedAt; finished_at=$actual.State.FinishedAt;
    actual_process_exited=($actual.State.Pid -eq 0); workflow_completion_credit=$false;
    log_path=$logPath; log_sha256=(Get-FileHash -LiteralPath $logPath).Hash.ToLowerInvariant();
    container_removed=$false
}
if (-not $terminal.actual_process_exited) { throw 'Native container process exit is unverified.' }
if ($probe.storage -eq 'container_layer') {
    $archive = Join-Path $probeDirectory "$receiptStem-native-output"
    if (Test-Path -LiteralPath $archive) { throw 'Native archive already exists; reconcile its inventory before another copy or removal.' }
    & docker cp "$($actual.Id):/probe" $archive
    if ($LASTEXITCODE -ne 0) { throw 'Native output copy failed; preserve stopped container and partial archive.' }
    $inventory = @(Get-ChildItem -LiteralPath $archive -File -Recurse | ForEach-Object {
        [ordered]@{path=[IO.Path]::GetRelativePath($archive,$_.FullName);size_bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    })
    if ($inventory.Count -eq 0) { throw 'Native archive is empty; preserve stopped container.' }
    $inventoryPath = Join-Path $probeDirectory "$receiptStem-native-archive.json"
    $inventory | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $inventoryPath -Encoding utf8
    $terminal.archive_path = $archive
    $terminal.archive_inventory_sha256 = (Get-FileHash -LiteralPath $inventoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $terminal.archive_file_count = $inventory.Count
}
# Remove only the exact stopped diagnostic container; retain the bind data/log.
$null = & docker rm $actual.Id
if ($LASTEXITCODE -ne 0) { throw 'Container cleanup response failed; retain receipt for reconciliation.' }
$terminal.container_removed = $true
$terminal | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding utf8
$terminal | ConvertTo-Json
