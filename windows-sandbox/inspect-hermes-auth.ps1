# Inspect the installed Hermes Agent inside the VM for dashboard/native API auth details.

param(
    [string]$VmName = "Wright-Hermes-Sandbox",
    [string]$Username = "User",
    [string]$Password = "password",
    [string]$OutputPath = (Join-Path $PSScriptRoot "hermes-auth-inspection.latest.txt")
)

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Output "Restarting this script as Administrator..."
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
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
    Exit 0
}

$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ($Username, $securePassword)

$results = Invoke-Command -VMName $VmName -Credential $cred -ScriptBlock {
    $ErrorActionPreference = "Continue"
    $root = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent"
    $patterns = @(
        "api/sessions",
        "/api/sessions",
        "Authorization",
        "Bearer",
        "dashboard",
        "session-key",
        "session_key",
        "api_key",
        "X-Hermes",
        "401"
    )

    "Hermes root: $root"
    ""
    "===== Matching Python Files ====="
    Get-ChildItem -Path $root -Recurse -Include *.py -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\venv\\Lib\\site-packages\\pip\\|\\__pycache__\\' } |
        Select-String -Pattern $patterns -SimpleMatch -ErrorAction SilentlyContinue |
        Select-Object Path, LineNumber, Line |
        Format-Table -AutoSize -Wrap |
        Out-String -Width 240

    ""
    "===== Hermes CLI Help ====="
    $hermes = Get-Command hermes -ErrorAction SilentlyContinue
    if ($hermes) {
        "hermes=$($hermes.Source)"
        try { & $hermes.Source dashboard --help 2>&1 | ForEach-Object { $_ } } catch { "dashboard help failed: $($_.Exception.Message)" }
        ""
        try { & $hermes.Source gateway --help 2>&1 | ForEach-Object { $_ } } catch { "gateway help failed: $($_.Exception.Message)" }
    } else {
        "hermes not found"
    }

    ""
    "===== Candidate Config/State Files ====="
    $paths = @(
        (Join-Path $env:LOCALAPPDATA "hermes"),
        (Join-Path $env:APPDATA "Hermes"),
        (Join-Path $env:USERPROFILE ".hermes")
    )
    foreach ($path in $paths) {
        "---- $path ----"
        if (Test-Path $path) {
            Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.Name -match 'token|auth|session|config|state|settings|dashboard' -and
                    $_.Length -lt 1048576
                } |
                Select-Object FullName, Length, LastWriteTime |
                Format-Table -AutoSize -Wrap |
                Out-String -Width 240
        } else {
            "missing"
        }
    }
}

$results | Set-Content -Path $OutputPath -Encoding UTF8
Write-Output "Hermes auth inspection written to $OutputPath"
