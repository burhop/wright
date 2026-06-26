$ErrorActionPreference = "Continue"
$secure = ConvertTo-SecureString "password" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("User", $secure)
Invoke-Command -VMName "Wright-Hermes-Sandbox" -Credential $cred -ScriptBlock {
    $ErrorActionPreference = "Continue"
    "--- netstat listening ---"
    netstat -ano | Select-String -Pattern "LISTENING" | ForEach-Object { $_.Line }
    "--- python/hermes processes ---"
    Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python|hermes|uvicorn' -or $_.CommandLine -match 'gateway|api.main|uvicorn|wright' } | Select-Object ProcessId,Name,CommandLine | Format-List | Out-String
} | Set-Content -Path "D:\repos\wright\windows-sandbox\gateway-ports.latest.txt" -Encoding UTF8
