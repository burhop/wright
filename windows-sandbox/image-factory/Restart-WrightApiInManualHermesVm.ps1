param(
    [string]$VmName = "wright-hermes-manual",
    [string]$GuestUsername = "wright",
    [string]$GuestPassword = "wright",
    [string]$WrightDir = "C:\wright",
    [string]$LlmApiUrl = ""
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdministrator)) {
    $arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`"",
        "-VmName", "`"$VmName`"",
        "-GuestUsername", "`"$GuestUsername`"",
        "-GuestPassword", "`"$GuestPassword`"",
        "-WrightDir", "`"$WrightDir`"",
        "-LlmApiUrl", "`"$LlmApiUrl`""
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to restart Wright in the VM."
    return
}

$securePassword = ConvertTo-SecureString $GuestPassword -AsPlainText -Force
$credential = [pscredential]::new($GuestUsername, $securePassword)

$vm = Get-VM -Name $VmName -ErrorAction Stop
$logRoot = if ($vm.Path) { $vm.Path } else { Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual") $VmName }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot "manual-vm-restart-wright-api.log"

Start-Transcript -Path $logPath -Force
try {
    if ($vm.State -ne "Running") {
        Start-VM -Name $VmName
    }

    Invoke-Command -VMName $VmName -Credential $credential -ArgumentList $WrightDir, $LlmApiUrl -ScriptBlock {
        param($WrightDir, $LlmApiUrl)
        $ErrorActionPreference = "Stop"

        $escapedWrightDir = [regex]::Escape($WrightDir)
        $currentPid = $PID
        Get-CimInstance Win32_Process |
            Where-Object {
                $_.ProcessId -ne $currentPid -and
                (
                    ($_.CommandLine -and $_.CommandLine -match $escapedWrightDir) -or
                    ($_.ExecutablePath -and $_.ExecutablePath -match $escapedWrightDir)
                )
            } |
            ForEach-Object {
                Write-Output "Stopping Wright process $($_.ProcessId): $($_.Name)"
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }

        $env:WRIGHT_LAUNCHED_BY_HERMES = "1"
        $env:FRONTEND_DIST_DIR = Join-Path $WrightDir "apps\web\dist"
        $env:WRIGHT_REPO_DIR = $WrightDir
        $env:HERMES_API_BASE_URL = "http://127.0.0.1:8642"
        $env:HERMES_API_KEY = "wright-local-dev"
        $env:API_SERVER_ENABLED = "true"
        $env:API_SERVER_HOST = "127.0.0.1"
        $env:API_SERVER_PORT = "8642"
        $env:API_SERVER_KEY = "wright-local-dev"
        if ($LlmApiUrl.Trim()) {
            [Environment]::SetEnvironmentVariable("LLM_API_URL", $LlmApiUrl, "User")
            $env:LLM_API_URL = $LlmApiUrl
        } else {
            [Environment]::SetEnvironmentVariable("LLM_API_URL", $null, "User")
            Remove-Item -Path "env:LLM_API_URL" -ErrorAction SilentlyContinue
        }

        $python = Join-Path $WrightDir ".venv\Scripts\python.exe"
        if (-not (Test-Path $python)) {
            throw "Wright venv Python not found: $python"
        }

        $tmpDir = Join-Path $WrightDir "tmp"
        New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
        $stdout = Join-Path $tmpDir "wright-api.stdout.log"
        $stderr = Join-Path $tmpDir "wright-api.stderr.log"
        $arguments = @(
            "-m", "uvicorn",
            "api.main:app",
            "--app-dir", (Join-Path $WrightDir "apps\api\src"),
            "--host", "127.0.0.1",
            "--port", "8000"
        )

        $process = Start-Process `
            -FilePath $python `
            -ArgumentList $arguments `
            -WorkingDirectory $WrightDir `
            -RedirectStandardOutput $stdout `
            -RedirectStandardError $stderr `
            -PassThru `
            -WindowStyle Hidden

        Set-Content -Path (Join-Path $tmpDir "wright-api.pid") -Value $process.Id -Encoding UTF8

        for ($i = 1; $i -le 30; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/setup/status" -UseBasicParsing -TimeoutSec 2
                Write-Output $response.Content
                return
            } catch {
                Start-Sleep -Seconds 1
            }
        }

        throw "Wright API did not respond after restart. Check $stderr"
    }

    Start-Process vmconnect.exe -ArgumentList "localhost `"$VmName`""
    Write-Output "Restarted Wright API in VM '$VmName'."
} finally {
    Stop-Transcript
}
