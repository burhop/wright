$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Assert-LastExitCode {
    param([string]$Label)

    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Push-Location $RootDir
try {
    Write-Host "== Git whitespace check =="
    git diff --check
    Assert-LastExitCode "Git whitespace check"

    Write-Host ""
    Write-Host "== Python pytest =="
    uv run pytest
    Assert-LastExitCode "Python pytest"

    Write-Host ""
    Write-Host "== Frontend Vitest =="
    npm run test --workspace=apps/web
    Assert-LastExitCode "Frontend Vitest"

    Write-Host ""
    Write-Host "== Frontend production build =="
    npm run build --workspace=apps/web
    Assert-LastExitCode "Frontend production build"

    Write-Host ""
    Write-Host "== MkDocs strict build =="
    uv run --with mkdocs-material mkdocs build --strict
    Assert-LastExitCode "MkDocs strict build"

    Write-Host ""
    Write-Host "== Security scans =="
    scripts/security-scan.ps1 -IncludeUntracked
    if (-not $?) {
        throw "Security scans failed"
    }

    Write-Host ""
    Write-Host "== Docker smoke test =="
    bash scripts/docker-smoke-test.sh
    Assert-LastExitCode "Docker smoke test"

    Write-Host ""
    Write-Host "Alpha release check passed."
} finally {
    Pop-Location
}
