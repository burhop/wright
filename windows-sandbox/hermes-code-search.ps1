$ErrorActionPreference = "Continue"
$secure = ConvertTo-SecureString "password" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("User", $secure)
Invoke-Command -VMName "Wright-Hermes-Sandbox" -Credential $cred -ScriptBlock {
  $root = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent"
  "root=$root"
  "--- api/sessions matches ---"
  Get-ChildItem -Path $root -Recurse -Include *.py -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\__pycache__\\|\\tests\\' } |
    Select-String -Pattern '/api/sessions','api/sessions','sessions' -SimpleMatch -ErrorAction SilentlyContinue |
    Select-Object Path,LineNumber,Line |
    Format-Table -AutoSize -Wrap | Out-String -Width 240
  "--- auth/header/dashboard matches ---"
  Get-ChildItem -Path $root -Recurse -Include *.py -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\__pycache__\\|\\tests\\' } |
    Select-String -Pattern 'Authorization','Bearer','401','dashboard','api_key','token','session-key','X-Hermes' -SimpleMatch -ErrorAction SilentlyContinue |
    Select-Object Path,LineNumber,Line |
    Format-Table -AutoSize -Wrap | Out-String -Width 240
} | Set-Content -Path "D:\repos\wright\windows-sandbox\hermes-code-search.latest.txt" -Encoding UTF8
