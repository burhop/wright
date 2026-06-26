$ErrorActionPreference = "Continue"
$secure = ConvertTo-SecureString "password" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("User", $secure)
$result = Invoke-Command -VMName "Wright-Hermes-Sandbox" -Credential $cred -ScriptBlock {
  $ErrorActionPreference = "Continue"
  "TIME=$(Get-Date -Format o)"
  "--- selected env ---"
  "HERMES_API_BASE_URL=$env:HERMES_API_BASE_URL"
  "HERMES_API_PORT=$env:HERMES_API_PORT"
  "HERMES_ACCEPT_HOOKS=$env:HERMES_ACCEPT_HOOKS"
  "WRIGHT_REPO_DIR=$env:WRIGHT_REPO_DIR"
  "--- hermes status ---"
  $h = Get-Command hermes -ErrorAction SilentlyContinue
  if ($h) {
    "hermes=$($h.Source)"
    & $h.Source gateway status 2>&1 | ForEach-Object { $_ }
  } else { "hermes not found" }
  "--- listening ports ---"
  netstat -ano | Select-String -Pattern "LISTENING|8000|8642|50350|42050" | ForEach-Object { $_.Line }
  "--- selected processes ---"
  Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'hermes|gateway|dashboard|uvicorn|api.main|wright' -or $_.Name -match 'Hermes|python|uvicorn' } | Select-Object ProcessId,Name,CommandLine | Format-List | Out-String
  "--- endpoint probes ---"
  $urls = @(
    "http://127.0.0.1:8000/api/health",
    "http://127.0.0.1:8000/api/agent/health",
    "http://127.0.0.1:8642/health",
    "http://127.0.0.1:8642/api/sessions"
  )
  foreach ($url in $urls) {
    try {
      $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3
      "$url -> $($r.StatusCode) $($r.Content.Substring(0, [Math]::Min(200, $r.Content.Length)))"
    } catch {
      "$url -> ERROR $($_.Exception.Message)"
    }
  }
}
$result | Set-Content -Path "D:\repos\wright\windows-sandbox\vm-gateway-current.latest.txt" -Encoding UTF8
