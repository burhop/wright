param(
    [switch]$IncludeUntracked,
    [switch]$SkipGitleaks,
    [switch]$SkipTruffleHog
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$GitleaksImage = if ($env:GITLEAKS_IMAGE) { $env:GITLEAKS_IMAGE } else { "ghcr.io/gitleaks/gitleaks:v8.30.1" }
$TruffleHogImage = if ($env:TRUFFLEHOG_IMAGE) { $env:TRUFFLEHOG_IMAGE } else { "ghcr.io/trufflesecurity/trufflehog:3.95.7" }

function Assert-LastExitCode {
    param([string]$Label)

    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
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

    if (-not $SkipGitleaks) {
        Write-Host ""
        Write-Host "== Gitleaks history scan =="
        docker run --rm `
            -v "${RootDir}:/repo" `
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
            -v "${RootDir}:/repo" `
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
}
