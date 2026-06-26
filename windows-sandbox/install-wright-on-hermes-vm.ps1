# Install Wright/plugin into an already-restored Hermes VM.
#
# Assumes the VM is at a good Hermes-installed state. This script does not
# restore checkpoints and does not run the Hermes Desktop installer.

param(
    [string]$VmName = "Wright-Hermes-Sandbox",
    [string]$GuestUsername = "User",
    [string]$GuestPassword = "password",
    [switch]$NoConnect,
    [switch]$NoExpose,
    [string]$ListenAddress = "127.0.0.1",
    [int]$HostPort = 18000,
    [int]$GuestPort = 8000,
    [string]$LlmApiUrl = "http://192.168.1.165:8000/v1"
)

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Output "Restarting this script as Administrator..."
    $argsList = @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "`"$PSCommandPath`"",
        "-VmName",
        "`"$VmName`"",
        "-GuestUsername",
        "`"$GuestUsername`"",
        "-GuestPassword",
        "`"$GuestPassword`"",
        "-ListenAddress",
        "`"$ListenAddress`"",
        "-HostPort",
        "$HostPort",
        "-GuestPort",
        "$GuestPort",
        "-LlmApiUrl",
        "`"$LlmApiUrl`""
    )
    if ($NoConnect) { $argsList += "-NoConnect" }
    if ($NoExpose) { $argsList += "-NoExpose" }
    Start-Process powershell.exe -Verb RunAs -ArgumentList $argsList
    Exit 0
}

if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: Hyper-V PowerShell cmdlets are not available."
    Exit 1
}

$vm = Get-VM -Name $VmName -ErrorAction Stop
if ($vm.State -ne "Running") {
    Start-VM -Name $VmName
}

if (-not $NoConnect) {
    Start-Process vmconnect.exe -ArgumentList "localhost", $VmName -ErrorAction SilentlyContinue
}

$securePassword = ConvertTo-SecureString $GuestPassword -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ($GuestUsername, $securePassword)

Write-Output "Waiting for VM guest PowerShell..."
$connected = $false
for ($i = 1; $i -le 40; $i++) {
    try {
        Invoke-Command -VMName $VmName -Credential $cred -ScriptBlock { Get-Date } -ErrorAction Stop | Out-Null
        $connected = $true
        break
    } catch {
        Write-Output "  Waiting for guest (attempt $i/40)... $($_.Exception.Message)"
        Start-Sleep -Seconds 5
    }
}
if (-not $connected) {
    Write-Error "ERROR: VM did not become responsive to PowerShell Direct."
    Exit 1
}

$workspaceDir = (Get-Item $PSScriptRoot).Parent.FullName
$tempZipPath = Join-Path $env:TEMP "wright-local.zip"
if (Test-Path $tempZipPath) {
    Remove-Item $tempZipPath -Force
}

Write-Output "Preparing current Wright repo archive..."
Push-Location $workspaceDir
tar -cf $tempZipPath `
    --exclude="node_modules" `
    --exclude=".venv" `
    --exclude=".git" `
    --exclude="windows-sandbox/.vm" `
    --exclude="tmp" `
    --exclude="*.log" `
    --exclude="*.pid" `
    --exclude="*.db" `
    --exclude="*.db-journal" `
    --exclude="*.db-wal" `
    --exclude="*.db-shm" `
    .
Pop-Location

$guestScriptPath = "C:\Users\Public\Downloads\provision-vm.ps1"
$guestZipPath = "C:\Users\Public\Downloads\wright.zip"
$localProvisionScript = Join-Path $PSScriptRoot "provision-vm.ps1"

Write-Output "Copying current repo and provisioner into VM..."
Copy-VMFile -VMName $VmName -SourcePath $localProvisionScript -DestinationPath $guestScriptPath -CreateFullPath -FileSource Host -Force
Copy-VMFile -VMName $VmName -SourcePath $tempZipPath -DestinationPath $guestZipPath -CreateFullPath -FileSource Host -Force
Remove-Item $tempZipPath -Force -ErrorAction SilentlyContinue

Write-Output "Installing Wright/plugin only; skipping Hermes Desktop setup..."
$oldEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
Invoke-Command -VMName $VmName -Credential $cred -ArgumentList $LlmApiUrl -ScriptBlock {
    param($LlmApiUrl)
    Set-ExecutionPolicy Bypass -Scope Process -Force
    $ErrorActionPreference = "Continue"
    & C:\Users\Public\Downloads\provision-vm.ps1 -SkipTools -SkipDesktop -LlmApiUrl $LlmApiUrl
} 2>&1 | Tee-Object -Variable provisionOutput | ForEach-Object { Write-Output $_ }
$ErrorActionPreference = $oldEAP

$provisionText = $provisionOutput | Out-String
if ($provisionText -match "ERROR:|WriteErrorException|Hermes CLI still reports") {
    Write-Error "ERROR: Wright/plugin provisioning failed."
    Exit 1
}

Write-Output "Creating fresh ready-to-run checkpoint..."
Get-VMSnapshot -VMName $VmName -Name "ready-to-run" -ErrorAction SilentlyContinue |
    Remove-VMSnapshot -Confirm:$false -ErrorAction SilentlyContinue
Checkpoint-VM -Name $VmName -SnapshotName "ready-to-run" | Out-Null

Write-Output "Starting Hermes Desktop launcher task inside VM..."
Invoke-Command -VMName $VmName -Credential $cred -AsJob -ArgumentList $LlmApiUrl -ScriptBlock {
    param($LlmApiUrl)
    Set-ExecutionPolicy Bypass -Scope Process -Force
    & C:\Users\Public\Downloads\provision-vm.ps1 -SkipTools -SkipWright -SkipDesktop -StartServers -LlmApiUrl $LlmApiUrl
} | Out-Null

if (-not $NoExpose) {
    $manageScript = Join-Path $PSScriptRoot "manage-vm.ps1"
    & $manageScript expose -VmName $VmName -ListenAddress $ListenAddress -HostPort $HostPort -GuestPort $GuestPort
}

Write-Output ""
Write-Output "Wright install on Hermes VM complete."
Write-Output "VM: $VmName"
Write-Output "Host API endpoint: http://${ListenAddress}:${HostPort}"
Write-Output "Open console: .\manage-vm.ps1 connect"
