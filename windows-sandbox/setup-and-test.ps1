# Windows Sandbox Automated Test Runner Script
# Runs inside the isolated sandbox to install dependencies and execute the test suites.

Write-Output "=== 1. Installing Chocolatey (Package Manager) ==="
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Update PATH for the current session to make 'choco' available immediately
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Output "=== 2. Installing Node.js, Python, and uv ==="
# Install packages via Chocolatey (force python 3.13)
choco install git nodejs-lts python3 --params "/InstallDir:C:\Python313" --version 3.13.0 -y
choco install uv -y

# Refresh Environment Variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Output "=== 3. Navigating to Wright Workspace ==="
cd C:\wright

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
    cd C:\wright
    $env:LLM_API_URL = "http://127.0.0.1:8000/v1" # Mock or local endpoint
    uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
}

$frontendJob = Start-Job -ScriptBlock {
    cd C:\wright
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
