# Collect diagnostics from the running Wright + Hermes VM without reprovisioning it.

param(
    [string]$VmName = "Wright-Hermes-Sandbox",
    [string]$Username = "User",
    [string]$Password = "password",
    [string]$OutputPath = (Join-Path $PSScriptRoot "vm-diagnostics.latest.txt")
)

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Output "Restarting this script as Administrator..."
    $argList = @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "`"$PSCommandPath`"",
        "-VmName",
        "`"$VmName`"",
        "-Username",
        "`"$Username`"",
        "-Password",
        "`"$Password`"",
        "-OutputPath",
        "`"$OutputPath`""
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $argList
    Exit 0
}

if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: Hyper-V PowerShell cmdlets are not available."
    Exit 1
}

$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ($Username, $securePassword)

$diagnostics = Invoke-Command -VMName $VmName -Credential $cred -ScriptBlock {
    $ErrorActionPreference = "Continue"

    function Section {
        param([string]$Title)
        ""
        "===== $Title ====="
    }

    Section "Environment"
    "USERPROFILE=$env:USERPROFILE"
    "WRIGHT_REPO_DIR=$env:WRIGHT_REPO_DIR"
    "WRIGHT_API_HOST=$env:WRIGHT_API_HOST"
    "WRIGHT_UI_MODE=$env:WRIGHT_UI_MODE"
    "HERMES_API_BASE_URL=$env:HERMES_API_BASE_URL"
    "HERMES_API_PORT=$env:HERMES_API_PORT"
    "HERMES_API_KEY_SET=$([bool]$env:HERMES_API_KEY)"

    Section "Hermes CLI"
    $hermes = Get-Command hermes -ErrorAction SilentlyContinue
    if ($hermes) {
        "hermes=$($hermes.Source)"
        try { & $hermes.Source --version 2>&1 | ForEach-Object { $_ } } catch { "version failed: $($_.Exception.Message)" }
        try { & $hermes.Source plugins list 2>&1 | ForEach-Object { $_ } } catch { "plugins list failed: $($_.Exception.Message)" }
    } else {
        "hermes not found on PATH"
    }

    Section "Processes"
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match 'Hermes|hermes|python|uvicorn|uv\.exe|node'
        } |
        Select-Object ProcessId, ParentProcessId, Name, CommandLine |
        Format-List |
        Out-String

    Section "Listening Ports"
    netstat -ano | Select-String -Pattern "LISTENING|8000|8642|18000|5173|3000|3001|1420|1421" | ForEach-Object { $_.Line }

    Section "Endpoint Probes"
    $urls = @(
        "http://127.0.0.1:8000/api/health",
        "http://127.0.0.1:8000/api/agent/health",
        "http://127.0.0.1:8642/health",
        "http://127.0.0.1:8642/api/sessions",
        "http://127.0.0.1:3000/health",
        "http://127.0.0.1:3001/health",
        "http://127.0.0.1:1420/health",
        "http://127.0.0.1:1421/health"
    )

    $loopbackPorts = netstat -ano |
        Select-String -Pattern '^\s+TCP\s+127\.0\.0\.1:(\d+)\s+0\.0\.0\.0:0\s+LISTENING\s+(\d+)' |
        ForEach-Object {
            if ($_.Line -match '^\s+TCP\s+127\.0\.0\.1:(\d+)\s+0\.0\.0\.0:0\s+LISTENING\s+(\d+)') {
                [int]$matches[1]
            }
        } |
        Sort-Object -Unique

    foreach ($port in $loopbackPorts) {
        foreach ($path in @("/", "/health", "/api/sessions", "/v1/models")) {
            $urls += "http://127.0.0.1:$port$path"
        }
    }

    foreach ($url in $urls) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            "$url -> $($response.StatusCode) $($response.Content.Substring(0, [Math]::Min(300, $response.Content.Length)))"
        } catch {
            "$url -> ERROR $($_.Exception.Message)"
        }
    }

    Section "Wright Logs Tail"
    $logPaths = @(
        "C:\wright\tmp\wright-api.log",
        "C:\wright\apps\api\wright.log"
    )
    foreach ($path in $logPaths) {
        "---- $path ----"
        if (Test-Path $path) {
            Get-Content -Path $path -Tail 80 -ErrorAction SilentlyContinue
        } else {
            "missing"
        }
    }
}

$diagnostics | Set-Content -Path $OutputPath -Encoding UTF8
Write-Output "Diagnostics written to $OutputPath"
