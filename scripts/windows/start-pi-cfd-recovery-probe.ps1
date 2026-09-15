param(
    [Parameter(Mandatory)][string]$ProbeDirectory,
    [Parameter(Mandatory)][string]$ContainerName,
    [ValidateSet('a','b')][string]$Alternative = 'a',
    [ValidateSet('prepare','solve')][string]$Operation = 'prepare',
    [ValidateRange(30,600)][int]$DeadlineSeconds = 600,
    [switch]$NativeStorage
)
$ErrorActionPreference = 'Stop'
$probeRepo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$probeRoot = (Resolve-Path -LiteralPath $ProbeDirectory).Path
$diagnosticRoot = [IO.Path]::GetFullPath((Join-Path $probeRepo 'artifacts/engineering-workflow-datasets/diagnostics'))
if (-not $probeRoot.StartsWith($diagnosticRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The diagnostic bind must be a dedicated directory under campaign diagnostics.'
}
if ($ContainerName -notmatch '^wright-pi-cfd-recovery-[a-z0-9-]+$') { throw 'Use a dedicated recovery container name.' }
$receiptStem = if ($Operation -eq 'prepare') { "container-$Alternative" } else { "container-$Alternative-solve" }
$receiptPath = Join-Path $probeRoot "$receiptStem.json"
if (Test-Path -LiteralPath $receiptPath) { throw 'Existing dispatch receipt must be reconciled; no replay.' }
$preflight = Get-Content -LiteralPath (Join-Path $probeRoot 'preflight.json') -Raw | ConvertFrom-Json
if (@($preflight.alternatives | Where-Object { $_.alternative -eq $Alternative -and $_.schema_status -eq 'passed' }).Count -ne 1) {
    throw 'The retained CAD contract has not passed its schema probe.'
}
$compilerHash = (Get-FileHash -LiteralPath (Join-Path $probeRoot 'pi_cfd_operations.py') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($compilerHash -ne $preflight.compiler_sha256) { throw 'Pinned compiler changed.' }
$probeImage = 'sha256:2f7f4bab1305671d0d622dd166070b24c21d3b81cd18730b3f3478a0b1d73b95'
$receipt = [ordered]@{
    schema_version=1; name=$ContainerName; image=$probeImage; ownership='owned';
    phase='create_intent'; at=[DateTimeOffset]::UtcNow.ToString('o');
    diagnostic_root=$probeRoot; compiler_sha256=$compilerHash; alternative=$Alternative;
    workflow_completion_credit=$false; network='none'; container_id=$null;
    operation=$Operation; deadline_seconds=$DeadlineSeconds; termination_grace_seconds=10
    storage=$(if ($NativeStorage) { 'container_layer' } else { 'windows_bind' })
}
$receipt | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding utf8
$probeMount = @()
if (-not $NativeStorage) { $probeMount = @('--mount', "type=bind,source=$probeRoot,target=/probe") }
$probeId = & docker create --name $ContainerName --label wright.purpose=engineering-cfd-recovery `
    --network none --cpus 2 --memory 6g --workdir /probe @probeMount `
    --entrypoint /usr/bin/timeout $probeImage --signal=TERM --kill-after=10s "$($DeadlineSeconds)s" `
    /opt/conda/envs/FoamAgent/bin/python /probe/pi_cfd_operations.py $Operation `
    --root /probe --contract "contract-$Alternative.json" --case "case-$Alternative"
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic container creation failed; reconcile receipt before retrying.' }
$receipt.container_id = $probeId.Trim()
$receipt.phase = 'created'
$receipt | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding utf8
if ($NativeStorage) {
    # Keep the entire native case off the Windows/9P filesystem. The stopped
    # container must be archived successfully before cleanup may remove it.
    & docker cp "$probeRoot/." "$($receipt.container_id):/probe"
    if ($LASTEXITCODE -ne 0) { throw 'Native input staging failed; preserve the exact created container receipt.' }
    $receipt.phase = 'inputs_staged'
    $receipt | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding utf8
}
$null = & docker start $receipt.container_id
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic container start response failed; outcome must be inspected.' }
$receipt.phase = 'started'
$receipt.started_at = [DateTimeOffset]::UtcNow.ToString('o')
$receipt | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding utf8
$receipt | ConvertTo-Json
