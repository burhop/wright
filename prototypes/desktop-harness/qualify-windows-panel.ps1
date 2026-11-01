param(
    [Parameter(Mandatory)][string]$StateDir,
    [Parameter(Mandatory)][string]$Python,
    [Parameter(Mandatory)][string]$NavigationInput,
    [Parameter(Mandatory)][string]$OutputDir,
    [string]$UsabilityInput
)

# Windows-local browser + actual MCP/storage qualification. This does not drive
# the OpenAI application or establish its panel/file/chat-switch acceptance.
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
if (-not $IsWindows) { throw 'Run this qualification on Windows.' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$StateDir = [IO.Path]::GetFullPath($StateDir)
$Python = [IO.Path]::GetFullPath($Python)
$NavigationInput = [IO.Path]::GetFullPath($NavigationInput)
if ($UsabilityInput) { $UsabilityInput = [IO.Path]::GetFullPath($UsabilityInput) }
foreach ($entry in @($repo, $StateDir, $Python, $NavigationInput, $OutputDir) + @($UsabilityInput | Where-Object { $_ })) {
    $full = [IO.Path]::GetFullPath($entry)
    if ($full.StartsWith('\\')) { throw 'Use local disk paths, not shares.' }
    $drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$([IO.Path]::GetPathRoot($full).TrimEnd('\'))'"
    if ($drive.DriveType -ne 3) { throw "A fixed local disk is required: $full" }
}
if (Test-Path $OutputDir) { throw 'Choose a fresh evidence directory; do not overwrite a receipt.' }
$output = [IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Path $output | Out-Null
$oldPython = $env:WRIGHT_PROBE_PYTHON
$oldBridge = $env:WRIGHT_PROBE_BRIDGE
Push-Location $repo
try {
    $env:WRIGHT_PROBE_PYTHON = (Resolve-Path $Python).Path
    $env:WRIGHT_PROBE_BRIDGE = Join-Path $repo 'prototypes/desktop-harness/mcp_bridge.py'
    $stamp = @{
        boundary = 'Windows-local browser, actual MCP/storage; simulated OpenAI host'
        commit = (git rev-parse HEAD)
        dirty = @(git status --short)
        windows = [Environment]::OSVersion.VersionString
        node = (node --version)
        python = (& $env:WRIGHT_PROBE_PYTHON --version)
        resource_sha256 = (Get-FileHash (Join-Path $PSScriptRoot 'native-editor.html') -Algorithm SHA256).Hash.ToLowerInvariant()
        native_panel = 'UNVERIFIED'
        native_download_open = 'UNVERIFIED'
        native_chat_return = 'UNVERIFIED'
    }
    $stamp | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 (Join-Path $output 'host.json')
    node (Join-Path $PSScriptRoot 'native_navigation_acceptance.mjs') $StateDir $NavigationInput (Join-Path $output 'navigation')
    if ($UsabilityInput) {
        node (Join-Path $PSScriptRoot 'native_usability_acceptance.mjs') $StateDir $UsabilityInput (Join-Path $output 'usability')
    }
} finally {
    $env:WRIGHT_PROBE_PYTHON = $oldPython
    $env:WRIGHT_PROBE_BRIDGE = $oldBridge
    Pop-Location
}
