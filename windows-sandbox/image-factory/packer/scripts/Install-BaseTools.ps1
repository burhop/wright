$ErrorActionPreference = "Stop"

function Refresh-Path {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

Write-Output "Installing base image tooling..."

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    Invoke-Expression ((New-Object Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))
}
Refresh-Path

choco install git nodejs-lts python3 -y --no-progress
Refresh-Path

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
}
Refresh-Path

git --version
node --version
python --version
uv --version

Write-Output "Base tools installed."
