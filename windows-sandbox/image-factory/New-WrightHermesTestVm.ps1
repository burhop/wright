param(
    [Parameter(Mandatory=$true)]
    [string]$ParentVhdx,

    [string]$VmName = "Wright-Hermes-Test",
    [string]$GuestUsername = "wrightadmin",

    [Parameter(Mandatory=$true)]
    [string]$GuestPassword,

    [string]$SwitchName = "Default Switch",
    [string]$LlmApiUrl = "http://127.0.0.1:8000/v1",
    [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\image-factory\runs")
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from an Administrator PowerShell on the Hyper-V host."
    }
}

function Wait-ForPowerShellDirect {
    param(
        [string]$VmName,
        [System.Management.Automation.PSCredential]$Credential,
        [int]$Attempts = 60
    )

    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            Invoke-Command -VMName $VmName -Credential $Credential -ScriptBlock { "ready" } -ErrorAction Stop | Out-Null
            return
        } catch {
            Write-Output "Waiting for guest PowerShell Direct ($i/$Attempts): $($_.Exception.Message)"
            Start-Sleep -Seconds 5
        }
    }

    throw "Guest did not become responsive to PowerShell Direct."
}

Assert-Administrator

if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
    throw "Hyper-V PowerShell cmdlets are not available."
}
if (-not (Test-Path $ParentVhdx)) {
    throw "Parent VHDX was not found: $ParentVhdx"
}
if (Get-VM -Name $VmName -ErrorAction SilentlyContinue) {
    throw "VM '$VmName' already exists. Remove it or choose a different -VmName."
}

$runRoot = New-Item -ItemType Directory -Path (Join-Path $OutputRoot $VmName) -Force
$childVhdx = Join-Path $runRoot.FullName "$VmName.diff.vhdx"
New-VHD -Path $childVhdx -ParentPath (Resolve-Path $ParentVhdx).Path -Differencing | Out-Null

New-VM -Name $VmName -MemoryStartupBytes 8GB -Generation 2 -VHDPath $childVhdx -Path $runRoot.FullName -SwitchName $SwitchName | Out-Null
Set-VM -Name $VmName -ProcessorCount 4
Set-VMMemory -VMName $VmName -DynamicMemoryEnabled $true
Enable-VMIntegrationService -VMName $VmName -Name "Guest Service Interface"

Start-VM -Name $VmName

$securePassword = ConvertTo-SecureString $GuestPassword -AsPlainText -Force
$credential = [pscredential]::new($GuestUsername, $securePassword)
Wait-ForPowerShellDirect -VmName $VmName -Credential $credential

$workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$archivePath = Join-Path $runRoot.FullName "wright-local.zip"
if (Test-Path $archivePath) {
    Remove-Item -Path $archivePath -Force
}

Push-Location $workspaceRoot
try {
    tar -cf $archivePath `
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
} finally {
    Pop-Location
}

$guestArchive = "C:\Users\Public\Downloads\wright.zip"
$guestInstallScript = "C:\Users\Public\Downloads\Install-WrightForHermesTest.ps1"
$guestTestScript = "C:\Users\Public\Downloads\Test-WrightHermesGuest.ps1"
Copy-VMFile -VMName $VmName -SourcePath $archivePath -DestinationPath $guestArchive -CreateFullPath -FileSource Host -Force
Copy-VMFile -VMName $VmName -SourcePath (Join-Path $PSScriptRoot "guest\Install-WrightForHermesTest.ps1") -DestinationPath $guestInstallScript -CreateFullPath -FileSource Host -Force
Copy-VMFile -VMName $VmName -SourcePath (Join-Path $PSScriptRoot "guest\Test-WrightHermesGuest.ps1") -DestinationPath $guestTestScript -CreateFullPath -FileSource Host -Force

Invoke-Command -VMName $VmName -Credential $credential -ArgumentList $LlmApiUrl -ScriptBlock {
    param($LlmApiUrl)
    Set-ExecutionPolicy Bypass -Scope Process -Force
    & "C:\Users\Public\Downloads\Install-WrightForHermesTest.ps1" -LlmApiUrl $LlmApiUrl
    & "C:\Users\Public\Downloads\Test-WrightHermesGuest.ps1"
} -ErrorAction Stop

Checkpoint-VM -Name $VmName -SnapshotName "wright-verified" | Out-Null

Write-Output ""
Write-Output "Disposable Wright + Hermes test VM verified."
Write-Output "  VM:        $VmName"
Write-Output "  Child VHD: $childVhdx"
Write-Output "  Checkpoint: wright-verified"
