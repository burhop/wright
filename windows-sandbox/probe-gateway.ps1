$ErrorActionPreference = "Continue"
$secure = ConvertTo-SecureString "password" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("User", $secure)
Invoke-Command -VMName "Wright-Hermes-Sandbox" -Credential $cred -ScriptBlock {
    $ErrorActionPreference = "Continue"
    "--- env ---"
    "HERMES_API_BASE_URL=$env:HERMES_API_BASE_URL"
    "HERMES_API_PORT=$env:HERMES_API_PORT"
    "--- netstat selected ---"
    netstat -ano | Select-String -Pattern "LISTENING|8000|8642|6856|python" | ForEach-Object { $_.Line }
    "--- probes ---"
    foreach ($url in @(
        "http://127.0.0.1:8642/health",
        "http://127.0.0.1:8642/api/sessions",
        "http://127.0.0.1:8000/api/agent/health",
        "http://127.0.0.1:8000/api/health"
    )) {
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
            "$url -> $($r.StatusCode) $($r.Content.Substring(0, [Math]::Min(500, $r.Content.Length)))"
        } catch {
            "$url -> ERROR $($_.Exception.Message)"
        }
    }
    "--- processes ---"
    Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python|hermes|uvicorn' -or $_.CommandLine -match 'gateway|api.main|uvicorn|wright' } | Select-Object ProcessId,Name,CommandLine | Format-List | Out-String
} | Set-Content -Path "D:\repos\wright\windows-sandbox\gateway-probes.latest.txt" -Encoding UTF8
