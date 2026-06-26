param(
    [string]$VmName = "wright-hermes-manual",
    [string]$GuestUsername = "wright",
    [string]$GuestPassword = "wright",
    [string]$LlmApiUrl = "",
    [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\manual")
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
        "-LlmApiUrl", "`"$LlmApiUrl`"",
        "-OutputRoot", "`"$OutputRoot`""
    )
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    Write-Output "Requested Administrator elevation. Accept the UAC prompt to install Wright in the VM."
    return
}

function Wait-ForPowerShellDirect {
    param(
        [string]$VmName,
        [System.Management.Automation.PSCredential]$Credential,
        [int]$Attempts = 90
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

$vm = Get-VM -Name $VmName -ErrorAction Stop
$runRoot = New-Item -ItemType Directory -Path (Join-Path $OutputRoot $VmName) -Force
$logPath = Join-Path $runRoot.FullName "manual-vm-wright-install.log"

Start-Transcript -Path $logPath -Force
try {
    if ($vm.State -ne "Running") {
        Start-VM -Name $VmName
    }

    Enable-VMIntegrationService -VMName $VmName -Name "Guest Service Interface" -ErrorAction SilentlyContinue

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
    $guestBaseToolsScript = "C:\Users\Public\Downloads\Install-BaseTools.ps1"
    $guestInstallScript = "C:\Users\Public\Downloads\Install-WrightForHermesTest.ps1"
    $guestTestScript = "C:\Users\Public\Downloads\Test-WrightHermesManualGuest.ps1"

    Copy-VMFile -VMName $VmName -SourcePath $archivePath -DestinationPath $guestArchive -CreateFullPath -FileSource Host -Force
    Copy-VMFile -VMName $VmName -SourcePath (Join-Path $PSScriptRoot "packer\scripts\Install-BaseTools.ps1") -DestinationPath $guestBaseToolsScript -CreateFullPath -FileSource Host -Force
    Copy-VMFile -VMName $VmName -SourcePath (Join-Path $PSScriptRoot "guest\Install-WrightForHermesTest.ps1") -DestinationPath $guestInstallScript -CreateFullPath -FileSource Host -Force
    Copy-VMFile -VMName $VmName -SourcePath (Join-Path $PSScriptRoot "guest\Test-WrightHermesManualGuest.ps1") -DestinationPath $guestTestScript -CreateFullPath -FileSource Host -Force

    Invoke-Command -VMName $VmName -Credential $credential -ArgumentList $LlmApiUrl -ScriptBlock {
        param($LlmApiUrl)
        $ErrorActionPreference = "Stop"
        Set-ExecutionPolicy Bypass -Scope Process -Force
        & "C:\Users\Public\Downloads\Install-BaseTools.ps1"
        & "C:\Users\Public\Downloads\Install-WrightForHermesTest.ps1" -LlmApiUrl $LlmApiUrl
        & "C:\Users\Public\Downloads\Test-WrightHermesManualGuest.ps1"
    } -ErrorAction Stop

    $snapshotName = "wright-installed-verified"
    $existingSnapshot = Get-VMSnapshot -VMName $VmName -Name $snapshotName -ErrorAction SilentlyContinue
    if (-not $existingSnapshot) {
        Checkpoint-VM -Name $VmName -SnapshotName $snapshotName | Out-Null
    }

    Write-Output ""
    Write-Output "Wright installed and verified in manual Hermes VM."
    Write-Output "  VM:         $VmName"
    Write-Output "  Checkpoint: $snapshotName"
} finally {
    Stop-Transcript
}
