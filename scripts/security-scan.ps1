param(
    [switch]$IncludeUntracked,
    [switch]$SkipGitleaks,
    [switch]$SkipTruffleHog
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ScanRoot = $RootDir
$TemporaryScanParent = $null
$GitleaksImage = if ($env:GITLEAKS_IMAGE) { $env:GITLEAKS_IMAGE } else { "ghcr.io/gitleaks/gitleaks:v8.30.1" }
$TruffleHogImage = if ($env:TRUFFLEHOG_IMAGE) { $env:TRUFFLEHOG_IMAGE } else { "ghcr.io/trufflesecurity/trufflehog:3.95.7" }

function Assert-LastExitCode {
    param([string]$Label)

    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Initialize-HistoryScanRoot {
    # A linked worktree's .git file points to a host-only common Git directory
    # that is not available inside the scanner container. Use a full local clone
    # for history scanners while the public-alpha scan retains live-tree coverage.
    if (Test-Path -LiteralPath (Join-Path $RootDir ".git") -PathType Leaf) {
        $script:TemporaryScanParent = Join-Path ([IO.Path]::GetTempPath()) ("wright-security-scan-" + [guid]::NewGuid().ToString("N"))
        $script:ScanRoot = Join-Path $script:TemporaryScanParent "repo"
        git clone --no-hardlinks --no-checkout $RootDir $script:ScanRoot | Out-Null
        Assert-LastExitCode "Linked-worktree history clone"
        $headCommit = (git -C $RootDir rev-parse --verify HEAD).Trim()
        Assert-LastExitCode "Resolve linked-worktree HEAD"
        git -C $script:ScanRoot checkout --detach $headCommit | Out-Null
        Assert-LastExitCode "Checkout linked-worktree HEAD"
    }

    $commitCount = [int](git -C $script:ScanRoot rev-list --count HEAD)
    Assert-LastExitCode "Count history scan commits"
    if ($commitCount -lt 1) {
        throw "History scan root contains no commits; refusing a false-green scan."
    }
    Write-Host "History scan coverage: $commitCount commits reachable from HEAD."
}

Push-Location $RootDir
try {
    Write-Host "== Wright public-alpha leak scan =="
    if ($IncludeUntracked) {
        python scripts/check-public-alpha-leaks.py --include-untracked
    } else {
        python scripts/check-public-alpha-leaks.py
    }
    Assert-LastExitCode "Public-alpha leak scan"

    if (-not $SkipGitleaks -or -not $SkipTruffleHog) {
        Initialize-HistoryScanRoot
    }

    if (-not $SkipGitleaks) {
        Write-Host ""
        Write-Host "== Gitleaks history scan =="
        docker run --rm `
            -v "${ScanRoot}:/repo" `
            $GitleaksImage `
            git /repo `
            --config /repo/.gitleaks.toml `
            --no-banner `
            --redact `
            --verbose
        Assert-LastExitCode "Gitleaks history scan"
    }

    if (-not $SkipTruffleHog) {
        Write-Host ""
        Write-Host "== TruffleHog history scan =="
        docker run --rm `
            -v "${ScanRoot}:/repo" `
            -w /repo `
            $TruffleHogImage `
            git file:///repo `
            --no-update `
            --fail `
            --results=verified,unknown `
            --no-verification `
            --exclude-globs=uv.lock,package-lock.json
        Assert-LastExitCode "TruffleHog history scan"
    }

    Write-Host ""
    Write-Host "Security scans passed."
} finally {
    Pop-Location
    if ($TemporaryScanParent -and (Test-Path -LiteralPath $TemporaryScanParent)) {
        Remove-Item -LiteralPath $TemporaryScanParent -Recurse -Force
    }
}
