param(
    [string]$VmName = "wright-hermes-manual",
    [string]$GuestUsername = "wright",
    [string]$GuestPassword = "wright"
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
        "-GuestPassword", "`"$GuestPassword`""
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to diagnose Hermes in the VM."
    return
}

$securePassword = ConvertTo-SecureString $GuestPassword -AsPlainText -Force
$credential = [pscredential]::new($GuestUsername, $securePassword)

$vm = Get-VM -Name $VmName -ErrorAction Stop
$logRoot = if ($vm.Path) { $vm.Path } else { Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual") $VmName }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot "manual-vm-hermes-api-diagnose.log"

Start-Transcript -Path $logPath -Force
try {
    if ($vm.State -ne "Running") {
        Start-VM -Name $VmName
    }

    Invoke-Command -VMName $VmName -Credential $credential -ScriptBlock {
        $ErrorActionPreference = "Continue"

        Write-Output "=== Processes ==="
        Get-CimInstance Win32_Process |
            Where-Object {
                ($_.Name -match "hermes|wright|python|node|uvicorn") -or
                ($_.CommandLine -match "hermes|wright|uvicorn|api\.main|8642")
            } |
            Select-Object ProcessId, Name, ExecutablePath, CommandLine |
            Format-List

        Write-Output "=== Listening Ports ==="
        Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
            Where-Object { $_.LocalPort -in 8000,8642,3001,3000,1421,1420 } |
            Sort-Object LocalPort |
            Select-Object LocalAddress, LocalPort, OwningProcess |
            Format-Table -AutoSize

        Write-Output "=== HTTP Probes ==="
        $headers = @{ Authorization = "Bearer wright-local-dev" }
        foreach ($url in @(
            "http://127.0.0.1:8000/api/setup/status",
            "http://127.0.0.1:8000/api/agent/sessions",
            "http://127.0.0.1:8642/health",
            "http://127.0.0.1:8642/api/sessions",
            "http://127.0.0.1:3001/health",
            "http://127.0.0.1:3000/health",
            "http://127.0.0.1:1421/health",
            "http://127.0.0.1:1420/health"
        )) {
            try {
                $response = Invoke-WebRequest -Uri $url -Headers $headers -UseBasicParsing -TimeoutSec 3
                $body = $response.Content
                if ($body.Length -gt 300) { $body = $body.Substring(0, 300) }
                Write-Output "$url -> $($response.StatusCode) $body"
            } catch {
                Write-Output "$url -> ERROR $($_.Exception.Message)"
            }
        }

        Write-Output "=== Hermes Environment Files ==="
        foreach ($path in @(
            "$env:USERPROFILE\.hermes\.env",
            "$env:LOCALAPPDATA\hermes\.env",
            "$env:LOCALAPPDATA\hermes\config.yaml",
            "$env:LOCALAPPDATA\hermes\hermes-agent\.env",
            "$env:LOCALAPPDATA\hermes\hermes-agent\config.yaml"
        )) {
            Write-Output "--- $path ---"
            if (Test-Path $path) {
                Get-Content -Path $path -ErrorAction Continue
            } else {
                Write-Output "(missing)"
            }
        }

        Write-Output "=== Hermes Logs Tail ==="
        $logDir = Join-Path $env:LOCALAPPDATA "hermes\logs"
        if (Test-Path $logDir) {
            Get-ChildItem -Path $logDir -File |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 5 |
                ForEach-Object {
                    Write-Output "--- $($_.FullName) ---"
                    Get-Content -Path $_.FullName -Tail 80 -ErrorAction Continue
                }
        } else {
            Write-Output "Hermes log directory missing: $logDir"
        }
    }

    Write-Output "Hermes API diagnostic complete for VM '$VmName'."
    Write-Output "Log: $logPath"
} finally {
    Stop-Transcript
}
