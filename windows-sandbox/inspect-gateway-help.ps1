$ErrorActionPreference = "Continue"
$secure = ConvertTo-SecureString "password" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("User", $secure)
Invoke-Command -VMName "Wright-Hermes-Sandbox" -Credential $cred -ScriptBlock {
    $ErrorActionPreference = "Continue"
    $hermes = Get-Command hermes -ErrorAction SilentlyContinue
    "hermes=$($hermes.Source)"
    "--- gateway help ---"
    & $hermes.Source gateway --help 2>&1 | ForEach-Object { $_ }
    "--- gateway status ---"
    & $hermes.Source gateway status 2>&1 | ForEach-Object { $_ }
    "--- gateway restart help maybe ---"
    & $hermes.Source gateway restart --help 2>&1 | ForEach-Object { $_ }
} | Set-Content -Path "D:\repos\wright\windows-sandbox\hermes-gateway-help.latest.txt" -Encoding UTF8
