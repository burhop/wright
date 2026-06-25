# Windows Sandbox Automated Test Runner Script
# Runs inside the isolated sandbox to install dependencies and execute the test suites.

# Prevent running on the host machine directly
$isSandbox = ($env:USERNAME -eq "WDAGUtilityAccount") -or (Get-Process -Name "CExecSvc" -ErrorAction SilentlyContinue)
if (-not $isSandbox) {
    Write-Error "[ERROR] This script is designed to run INSIDE Windows Sandbox. To start the sandbox, please configure and double-click the 'test-windows.wsb' file on your host machine instead."
    Exit 1
}

Write-Output "=== 1. Installing Chocolatey (Package Manager) ==="
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Update PATH for the current session to make 'choco' available immediately
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Output "=== 2. Installing Node.js, Python, and uv ==="
# Install packages via Chocolatey
choco install git -y
choco install nodejs-lts -y
choco install python3 --params "/InstallDir:C:\Python313" --version 3.13.0 -y

# Install uv using official installer script
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Refresh Environment Variables and include uv's install location
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User") + ";$env:USERPROFILE\.local\bin"

Write-Output "=== 3. Copying Repo to Local Sandbox Path ==="
# Mapped folders don't support symlinks (npm workspaces need them).
# Copy to a local path inside the sandbox for full NTFS support.
xcopy C:\wright C:\wright-local /E /I /H /Y /Q
cd C:\wright-local

Write-Output "=== 4. Setting up Python Virtual Environment (uv sync) ==="
uv sync --all-packages

Write-Output "=== 5. Installing Node Modules ==="
npm install

Write-Output "=== 6. Installing Playwright browsers ==="
npx playwright install chromium --with-deps

Write-Output "=== 7. Running Backend Pytest Suite ==="
uv run pytest

Write-Output "=== 8. Running Frontend Vitest Suite ==="
npm run test --workspace=apps/web

Write-Output "=== 9. Running Playwright Integration Tests ==="
# Run the API and frontend servers in the background
$backendJob = Start-Job -ScriptBlock {
    cd C:\wright-local
    $env:LLM_API_URL = "http://127.0.0.1:8000/v1" # Mock or local endpoint
    uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
}

$frontendJob = Start-Job -ScriptBlock {
    cd C:\wright-local
    npm run dev --workspace=apps/web -- --host
}

Write-Output "Waiting for servers to boot..."
Start-Sleep -Seconds 10

# Run Playwright tests
npx playwright test

Write-Output "=== 10. Cleaning up Background Jobs ==="
Stop-Job $backendJob
Stop-Job $frontendJob

Write-Output "=========================================="
Write-Output "Testing complete. You can close this window."
Write-Output "=========================================="

# Keep window open for inspection
pause
