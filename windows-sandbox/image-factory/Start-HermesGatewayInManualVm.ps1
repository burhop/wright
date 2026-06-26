param(
    [string]$VmName = "wright-hermes-manual",
    [string]$GuestUsername = "wright",
    [string]$GuestPassword = "wright",
    [string]$ApiServerKey = "wright-local-dev",
    [int]$ApiServerPort = 8642
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
        "-ApiServerKey", "`"$ApiServerKey`"",
        "-ApiServerPort", "$ApiServerPort"
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to start Hermes Gateway in the VM."
    return
}

$securePassword = ConvertTo-SecureString $GuestPassword -AsPlainText -Force
$credential = [pscredential]::new($GuestUsername, $securePassword)

$vm = Get-VM -Name $VmName -ErrorAction Stop
$logRoot = if ($vm.Path) { $vm.Path } else { Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual") $VmName }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$logPath = Join-Path $logRoot "manual-vm-start-hermes-gateway.log"

Start-Transcript -Path $logPath -Force
try {
    if ($vm.State -ne "Running") {
        Start-VM -Name $VmName
    }

    Invoke-Command -VMName $VmName -Credential $credential -ArgumentList $ApiServerKey, $ApiServerPort -ScriptBlock {
        param($ApiServerKey, $ApiServerPort)
        $ErrorActionPreference = "Stop"

        $settings = @(
            "API_SERVER_ENABLED=true",
            "API_SERVER_HOST=127.0.0.1",
            "API_SERVER_PORT=$ApiServerPort",
            "API_SERVER_KEY=$ApiServerKey"
        )

        $envPaths = @(
            (Join-Path $env:LOCALAPPDATA "hermes\.env"),
            (Join-Path $env:USERPROFILE ".hermes\.env")
        )
        foreach ($envPath in $envPaths) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $envPath) -Force | Out-Null
            Set-Content -Path $envPath -Value $settings -Encoding UTF8
            Write-Output "Wrote Hermes API settings to $envPath"
        }

        $hermes = Get-Command hermes -ErrorAction Stop
        $tmpDir = "C:\wright\tmp"
        New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

        try {
            & $hermes.Source gateway install
            if ($LASTEXITCODE -ne 0) {
                throw "hermes gateway install exited with $LASTEXITCODE"
            }
            Write-Output "Hermes Gateway install command completed."
        } catch {
            Write-Warning "Gateway install failed; starting gateway run hidden. $($_.Exception.Message)"
            $stdout = Join-Path $tmpDir "hermes-gateway.stdout.log"
            $stderr = Join-Path $tmpDir "hermes-gateway.stderr.log"
            $process = Start-Process `
                -FilePath $hermes.Source `
                -ArgumentList @("gateway", "run") `
                -WorkingDirectory $tmpDir `
                -RedirectStandardOutput $stdout `
                -RedirectStandardError $stderr `
                -PassThru `
                -WindowStyle Hidden
            Set-Content -Path (Join-Path $tmpDir "hermes-gateway.pid") -Value $process.Id -Encoding UTF8
            Write-Output "Started Hermes Gateway process $($process.Id)."
        }

        $headers = @{ Authorization = "Bearer $ApiServerKey" }
        for ($i = 1; $i -le 20; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:$ApiServerPort/health" -Headers $headers -UseBasicParsing -TimeoutSec 2
                Write-Output "Hermes Gateway health: HTTP $($response.StatusCode) $($response.Content)"
                return
            } catch {
                Start-Sleep -Seconds 1
            }
        }

        throw "Hermes Gateway did not respond on http://127.0.0.1:$ApiServerPort/health"
    }

    Write-Output "Hermes Gateway start completed for VM '$VmName'."
    Write-Output "Log: $logPath"
} finally {
    Stop-Transcript
}
