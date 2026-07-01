param(
    [switch]$Rebuild,
    [switch]$RestartAll,
    [string]$ComposeFile = "docker-compose.hackathon.yml",
    [string]$LogFile = "tmp\nous-hackathon-update.log"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogPath = Join-Path $RepoRoot $LogFile
$LogDir = Split-Path $LogPath -Parent
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Push-Location $RepoRoot
try {
    $previousComposeFile = $env:COMPOSE_FILE
    $previousLogFile = $env:LOG_FILE
    $env:COMPOSE_FILE = $ComposeFile
    $env:LOG_FILE = ($LogFile -replace "\\", "/")

    $bashArgs = @("scripts/hackathon-update-wright.sh")
    if ($Rebuild) {
        $bashArgs += "--rebuild"
    }
    elseif ($RestartAll) {
        $bashArgs += "--restart-all"
    }

    & bash @bashArgs
    exit $LASTEXITCODE
}
finally {
    if ($null -eq $previousComposeFile) {
        Remove-Item Env:\COMPOSE_FILE -ErrorAction SilentlyContinue
    }
    else {
        $env:COMPOSE_FILE = $previousComposeFile
    }

    if ($null -eq $previousLogFile) {
        Remove-Item Env:\LOG_FILE -ErrorAction SilentlyContinue
    }
    else {
        $env:LOG_FILE = $previousLogFile
    }

    Pop-Location
}
