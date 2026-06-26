# Unified VM Test Automation: Wright + Hermes Desktop
# ===================================================
# Run this script on your Windows 11 Host machine (as Administrator).
#
# This script does it all:
# 1. Checks if the Hyper-V VM "Wright-Hermes-Sandbox" is created.
# 2. If not, automatically downloads Microsoft's Win11 Dev VM, creates, and configures it.
# 3. Boots the VM.
# 4. Connects via PowerShell Direct using default Win11 Dev VM credentials (User / P@ssw0rd!).
# 5. Automatically copies and runs the provisioning script inside the VM.
# 6. Starts the backend servers and launches Hermes Desktop inside the VM.
# 7. Opens the interactive VM console window on your host desktop.

param(
    [string]$VmName = "Wright-Hermes-Sandbox",
    [string]$ImagePath,  # Optional local path to downloaded Win11 VHDX or ZIP file
    [switch]$SkipDownload,
    [switch]$HermesAlreadyInstalled,
    [switch]$UseExistingVm,
    [switch]$BaseOnly,
    [switch]$NoConnect,
    [switch]$NoExpose,
    [string]$ListenAddress = "127.0.0.1",
    [int]$HostPort = 18000,
    [int]$GuestPort = 8000,
    [string]$GuestUsername = "User",
    [string]$GuestPassword = "P@ssw0rd!",
    [string]$LlmApiUrl = "http://192.168.1.165:8000/v1",
    [string]$HermesSetupUrl = "https://hermes-assets.nousresearch.com/Hermes-Setup.exe",
    [switch]$AllowCredentialPrompt
)

$ErrorActionPreference = "Stop"

# ---- 1. Ensure Admin Rights on Host ----
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "ERROR: This script must be run as Administrator on your host machine to manage Hyper-V VMs."
    Write-Output "Please open PowerShell as Administrator and run the script again."
    Exit 1
}

# ---- 2. Verify Hyper-V is Enabled ----
if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
    Write-Output "Hyper-V cmdlets not found. Attempting to enable Hyper-V..."
    try {
        $featureResult = Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart
        if ($featureResult.RestartNeeded) {
            Write-Warning "Hyper-V was successfully enabled, but your system requires a restart to activate the hypervisor and load the PowerShell cmdlets."
            Write-Warning "Please restart your computer and run this script again."
            Exit 0
        }
    } catch {
        Write-Error "ERROR: Failed to enable Hyper-V. Please enable it manually in Windows Features."
        Exit 1
    }

    # Try to import the module in case it just needs loading
    Import-Module Hyper-V -ErrorAction SilentlyContinue
    if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
        Write-Warning "Hyper-V has been enabled, but the cmdlets are not available in the current session."
        Write-Warning "Please restart your computer or open a new Administrator PowerShell window and run this script again."
        Exit 0
    }
}

# ---- 3. Check VM and checkpoint state ----
$VM = Get-VM -Name $VmName -ErrorAction SilentlyContinue
$VnExists = $null -ne $VM

$hasToolsCheckpoint = $false
$hasBaseCheckpoint = $false
$hasHermesCheckpoint = $false
$hasReadyCheckpoint = $false
if ($VnExists) {
    $hasBaseCheckpoint = $null -ne (Get-VMSnapshot -VMName $VmName -Name "base-ready" -ErrorAction SilentlyContinue)
    $hasToolsCheckpoint = $null -ne (Get-VMSnapshot -VMName $VmName -Name "tools-ready" -ErrorAction SilentlyContinue)
    $hasHermesCheckpoint = $null -ne (Get-VMSnapshot -VMName $VmName -Name "hermes-installed" -ErrorAction SilentlyContinue)
    $hasReadyCheckpoint  = $null -ne (Get-VMSnapshot -VMName $VmName -Name "ready-to-run" -ErrorAction SilentlyContinue)
}

# If Hermes has already been manually installed and snapshotted, use that as
# the fastest stable base for plugin iteration. If it was just installed
# manually, preserve the current VM state before touching Wright/plugin files.
if ($VnExists -and $HermesAlreadyInstalled -and $hasHermesCheckpoint) {
    Write-Output "VM '$VmName' found. Reverting to 'hermes-installed' checkpoint for Wright/plugin install..."
    Stop-VM -Name $VmName -Force -ErrorAction SilentlyContinue
    if ($hasReadyCheckpoint) {
        Remove-VMSnapshot -VMName $VmName -Name "ready-to-run" -ErrorAction SilentlyContinue
    }
    Restore-VMSnapshot -VMName $VmName -Name "hermes-installed" -Confirm:$false
    Start-VM -Name $VmName
    Write-Output "Reverted to 'hermes-installed'. Continuing with Wright/plugin setup..."
} elseif ($VnExists -and $HermesAlreadyInstalled) {
    Write-Output "VM '$VmName' found with -HermesAlreadyInstalled. Preserving current state as 'hermes-installed'..."
    if ($hasReadyCheckpoint) {
        Remove-VMSnapshot -VMName $VmName -Name "ready-to-run" -ErrorAction SilentlyContinue
    }
    Checkpoint-VM -Name $VmName -SnapshotName "hermes-installed" | Out-Null
    $hasHermesCheckpoint = $true
    Write-Output "'hermes-installed' checkpoint saved from the current VM state."
} elseif ($VnExists -and $hasToolsCheckpoint) {
    Write-Output "VM '$VmName' found. Reverting to 'tools-ready' checkpoint for a clean Wright + Hermes install..."
    Stop-VM -Name $VmName -Force -ErrorAction SilentlyContinue
    if ($hasReadyCheckpoint) {
        Remove-VMSnapshot -VMName $VmName -Name "ready-to-run" -ErrorAction SilentlyContinue
    }
    Restore-VMSnapshot -VMName $VmName -Name "tools-ready" -Confirm:$false
    Start-VM -Name $VmName
    Write-Output "Reverted to 'tools-ready'. Continuing with Wright + Hermes setup..."
} elseif ($VnExists -and $hasBaseCheckpoint) {
    Write-Output "VM '$VmName' found. Reverting to 'base-ready' checkpoint for tools + Hermes install..."
    Stop-VM -Name $VmName -Force -ErrorAction SilentlyContinue
    Restore-VMSnapshot -VMName $VmName -Name "base-ready" -Confirm:$false
    Start-VM -Name $VmName
    Write-Output "Reverted to 'base-ready'. Continuing with tools + Hermes setup..."
} elseif ($VnExists -and -not $hasToolsCheckpoint -and $UseExistingVm) {
    Write-Output "VM '$VmName' exists with no checkpoints. -UseExistingVm was specified, so preserving it and continuing provisioning..."
} elseif ($VnExists -and -not $hasToolsCheckpoint) {
    Write-Output "VM '$VmName' exists but has no checkpoints (incomplete setup). Recreating..."
    Stop-VM -Name $VmName -Force -ErrorAction SilentlyContinue
    Remove-VM -Name $VmName -Force
    $VnExists = $false
}

if (-not $VnExists) {
    Write-Output "VM '$VmName' not found. Starting VM creation process..."
    
    $WorkspaceDir = (Get-Item $PSScriptRoot).Parent.FullName
    $VMDir = Join-Path $WorkspaceDir "windows-sandbox\.vm"
    if (-not (Test-Path $VMDir)) {
        New-Item -ItemType Directory -Path $VMDir | Out-Null
    }

    $VHDXFile = $null

    if ($ImagePath) {
        if (-not (Test-Path $ImagePath)) {
            Write-Error "ERROR: Specified ImagePath '$ImagePath' does not exist."
            Exit 1
        }
        if ($ImagePath -like "*.zip") {
            Write-Output "Extracting specified ZIP file: $ImagePath..."
            Expand-Archive -Path $ImagePath -DestinationPath $VMDir -Force
            $VHDXFile = Get-ChildItem -Path $VMDir -Filter "*.vhdx" -Recurse | Select-Object -First 1
        } elseif ($ImagePath -like "*.vhdx") {
            $VHDXFile = $ImagePath
        } else {
            Write-Error "ERROR: ImagePath must point to a .zip or .vhdx file."
            Exit 1
        }
    } else {
        # Check if a VHDX already exists in the .vm folder
        $existingVhd = Get-ChildItem -Path $VMDir -Filter "*.vhdx" -Recurse | Select-Object -First 1
        if ($existingVhd) {
            Write-Output "Found existing VHDX at: $($existingVhd.FullName)"
            $VHDXFile = $existingVhd.FullName
        } elseif (-not $SkipDownload) {
            Write-Output "============================================"
            Write-Output "  Downloading Windows 11 Developer VM Image"
            Write-Output "  Note: This is a ~20GB download."
            Write-Output "============================================"
            
            $ZipPath = Join-Path $VMDir "Win11DevVM.zip"
            $DownloadUrl = "https://aka.ms/windev_VM_hyperv"
            
            Write-Output "Downloading from $DownloadUrl..."
            Start-BitsTransfer -Source $DownloadUrl -Destination $ZipPath -DisplayName "Downloading Windows 11 VM"
            
            Write-Output "Extracting VM image..."
            Expand-Archive -Path $ZipPath -DestinationPath $VMDir -Force
            Remove-Item $ZipPath -Force
            
            $VHDXFile = Get-ChildItem -Path $VMDir -Filter "*.vhdx" -Recurse | Select-Object -First 1
        } else {
            Write-Error "ERROR: No image found and -SkipDownload is set."
            Exit 1
        }
    }

    if (-not $VHDXFile) {
        Write-Error "ERROR: Could not find any .vhdx file in the VM directory."
        Exit 1
    }

    $VHDXPath = if ($VHDXFile -is [System.IO.FileInfo]) { $VHDXFile.FullName } else { $VHDXFile }
    
    # Copy VHDX to a VM path
    $VhdDestDir = Join-Path $VMDir "Virtual Hard Disks"
    if (-not (Test-Path $VhdDestDir)) { New-Item -ItemType Directory -Path $VhdDestDir | Out-Null }
    $VhdDestPath = Join-Path $VhdDestDir "$VmName.vhdx"
    Write-Output "Copying VHDX to VM storage path..."
    Copy-Item -Path $VHDXPath -Destination $VhdDestPath -Force

    # Create VM
    Write-Output "Creating VM '$VmName'..."
    New-VM -Name $VmName -MemoryStartupBytes 4GB -Generation 2 -VHDPath $VhdDestPath -Path $VMDir -SwitchName "Default Switch" | Out-Null
    Set-VM -Name $VmName -ProcessorCount 4
    Set-VMMemory -VMName $VmName -DynamicMemoryEnabled $true
    Enable-VMIntegrationService -VMName $VmName -Name "Guest Service Interface"
    
    $VM = Get-VM -Name $VmName
    Write-Output "VM '$VmName' created successfully."
} else {
    Write-Output "VM '$VmName' already exists. Reusing existing virtual machine."
}

# ---- 4. Start VM ----
if ($VM.State -ne "Running") {
    Write-Output "Starting VM '$VmName'..."
    Start-VM -Name $VmName
} else {
    Write-Output "VM '$VmName' is already running."
}

# Open VM Connection console only when requested by default behavior. Use
# -NoConnect when running repeated provisioning tests and open the console later
# with manage-vm.ps1 connect.
if (-not $NoConnect) {
    Write-Output "Opening VM Connection Console so you can monitor the boot process..."
    Start-Process vmconnect.exe -ArgumentList "localhost", $VmName -ErrorAction SilentlyContinue
} else {
    Write-Output "Skipping VM Connection Console because -NoConnect was specified."
}

# ---- 5. Establish PowerShell Direct Connection ----
Write-Output "Establishing connection to VM guest OS..."
$password = ConvertTo-SecureString $GuestPassword -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ($GuestUsername, $password)
$credentialCandidates = New-Object System.Collections.Generic.List[object]

function Add-CredentialCandidate {
    param(
        [Parameter(Mandatory=$true)][string]$Username,
        [Parameter(Mandatory=$true)][string]$Password
    )

    $exists = $credentialCandidates | Where-Object {
        $_.Username -eq $Username -and $_.Password -eq $Password
    } | Select-Object -First 1
    if (-not $exists) {
        $credentialCandidates.Add([PSCustomObject]@{ Username = $Username; Password = $Password }) | Out-Null
    }
}

Add-CredentialCandidate -Username $GuestUsername -Password $GuestPassword
foreach ($knownPassword in @("password", "Passw0rd!", "P@ssw0rd!")) {
    Add-CredentialCandidate -Username "User" -Password $knownPassword
    Add-CredentialCandidate -Username ".\User" -Password $knownPassword
}
$credentialIndex = 0

function Test-GuestPowerShellDirect {
    param(
        [Parameter(Mandatory=$true)][string]$VmName,
        [Parameter(Mandatory=$true)][System.Management.Automation.PSCredential]$Credential,
        [int]$TimeoutSeconds = 20
    )

    $job = $null
    try {
        $job = Invoke-Command -VMName $VmName -Credential $Credential -ScriptBlock { Get-Date } -AsJob -ErrorAction Stop
        $completed = Wait-Job -Job $job -Timeout $TimeoutSeconds
        if (-not $completed) {
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            return [PSCustomObject]@{
                Success = $false
                Error = "PowerShell Direct connection attempt timed out after $TimeoutSeconds seconds."
                TimedOut = $true
            }
        }

        $receiveErrors = @()
        Receive-Job -Job $job -ErrorAction SilentlyContinue -ErrorVariable receiveErrors | Out-Null
        if ($job.State -eq "Completed" -and $receiveErrors.Count -eq 0) {
            return [PSCustomObject]@{ Success = $true; Error = $null; TimedOut = $false }
        }

        $message = if ($receiveErrors.Count -gt 0) {
            ($receiveErrors | ForEach-Object { $_.Exception.Message }) -join " "
        } else {
            "PowerShell Direct job ended with state $($job.State)."
        }
        return [PSCustomObject]@{ Success = $false; Error = $message; TimedOut = $false }
    } catch {
        return [PSCustomObject]@{ Success = $false; Error = $_.Exception.Message; TimedOut = $false }
    } finally {
        if ($job) {
            Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        }
    }
}

function Wait-ForGuestPowerShell {
    param(
        [string]$VmName,
        [System.Management.Automation.PSCredential]$Credential,
        [int]$Attempts = 40
    )

    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            Invoke-Command -VMName $VmName -Credential $Credential -ScriptBlock { Get-Date } -ErrorAction Stop | Out-Null
            return $true
        } catch {
            Write-Output "  Waiting for guest PowerShell (attempt $i/$Attempts)... $($_.Exception.Message)"
            Start-Sleep -Seconds 5
        }
    }
    return $false
}

Write-Output "Waiting for Windows guest OS to boot and become responsive..."
$connected = $false
$currentCred = $cred
for ($i = 1; $i -le 40; $i++) {
    $connectionResult = Test-GuestPowerShellDirect -VmName $VmName -Credential $currentCred
    if ($connectionResult.Success) {
        $connected = $true
        $cred = $currentCred # Save the working credentials to be used by subsequent steps
        break
    }

    $err = $connectionResult.Error
    if ($err -like "*credential*") {
        $credentialIndex += 1
        if ($credentialIndex -lt $credentialCandidates.Count) {
            $candidate = $credentialCandidates[$credentialIndex]
            Write-Output "  Credentials rejected; retrying as $($candidate.Username) with next known test password..."
            $candidatePassword = ConvertTo-SecureString $candidate.Password -AsPlainText -Force
            $currentCred = New-Object System.Management.Automation.PSCredential ($candidate.Username, $candidatePassword)
        } else {
            if ($AllowCredentialPrompt) {
                Write-Output ""
                Write-Warning "The known test credentials were rejected by the VM."
                Write-Output "Please provide the username and password of the account you logged into inside the VM."
                $user = Read-Host "Username (default: User)"
                if ([string]::IsNullOrEmpty($user)) { $user = "User" }
                $passStr = Read-Host -AsSecureString "Password"
                $currentCred = New-Object System.Management.Automation.PSCredential ($user, $passStr)
                Write-Output "Retrying connection with entered credentials..."
            } else {
                $triedCredentials = ($credentialCandidates | ForEach-Object { $_.Username + '/' + $_.Password }) -join ', '
                Write-Error "ERROR: Known VM credentials were rejected. Tried: $triedCredentials. Rerun with -GuestUsername/-GuestPassword or -AllowCredentialPrompt for manual entry."
                Exit 1
            }
        }
    } else {
        Write-Output "  Waiting for boot (attempt $i/40)... [Diagnostic: $err]"
        Start-Sleep -Seconds 5
    }
}

if (-not $connected) {
    Write-Error "ERROR: VM did not become responsive to PowerShell Direct within the timeout period. This means the base image is not ready for unattended provisioning yet."
    Write-Output "Open an elevated Hyper-V console, complete any first-login/OOBE steps, verify the local account credentials, then create or rerun from a bootstrap checkpoint."
    Write-Output "If the image uses non-default credentials, rerun with -GuestUsername/-GuestPassword. For manual rescue only, add -AllowCredentialPrompt."
    Exit 1
}
Write-Output "Connection established successfully!"

if (-not $hasBaseCheckpoint -and -not $hasToolsCheckpoint -and -not $HermesAlreadyInstalled) {
    Write-Output "Creating checkpoint 'base-ready'..."
    Stop-VM -Name $VmName -Force
    Get-VMSnapshot -VMName $VmName -Name "base-ready" -ErrorAction SilentlyContinue |
        Remove-VMSnapshot -Confirm:$false -ErrorAction SilentlyContinue
    Checkpoint-VM -Name $VmName -SnapshotName "base-ready" | Out-Null
    Start-VM -Name $VmName
    $hasBaseCheckpoint = $true
    Write-Output "'base-ready' checkpoint saved."

    if (-not (Wait-ForGuestPowerShell -VmName $VmName -Credential $cred -Attempts 40)) {
        Write-Error "ERROR: VM did not come back after base-ready checkpoint."
        Exit 1
    }
}

if ($BaseOnly) {
    Write-Output ""
    Write-Output "=============================================================="
    Write-Output "  Base VM Ready"
    Write-Output "=============================================================="
    Write-Output "  - Checkpoint: base-ready"
    Write-Output "  - PowerShell Direct verified for the supplied guest credentials."
    Write-Output "  - Rerun without -BaseOnly to install tools, Hermes Desktop, and Wright."
    Write-Output "=============================================================="
    Exit 0
}

function Test-GuestHermesBase {
    param(
        [string]$VmName,
        [System.Management.Automation.PSCredential]$Credential
    )

    try {
        Invoke-Command -VMName $VmName -Credential $Credential -ScriptBlock {
            $searchRoots = @(
                (Join-Path $env:LOCALAPPDATA "hermes"),
                (Join-Path $env:LOCALAPPDATA "Programs"),
                $env:ProgramFiles,
                ${env:ProgramFiles(x86)}
            )
            $hermesExe = $null
            foreach ($root in ($searchRoots | Where-Object { $_ } | Select-Object -Unique)) {
                if (Test-Path $root) {
                    $hermesExe = Get-ChildItem -Path $root -Filter "Hermes.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
                    if ($hermesExe) { break }
                }
            }
            if (-not $hermesExe) {
                throw "Hermes.exe was not found."
            }
            $envPath = Join-Path $env:USERPROFILE ".hermes\.env"
            if (-not (Test-Path $envPath)) {
                throw "Hermes .env was not found at $envPath."
            }
            $envText = Get-Content -Path $envPath -Raw
            foreach ($expected in @("API_SERVER_ENABLED=true", "API_SERVER_PORT=8642", "API_SERVER_KEY=wright-local-dev")) {
                if ($envText -notmatch [regex]::Escape($expected)) {
                    throw "Hermes API server setting missing: $expected"
                }
            }
            Write-Output "Hermes base verified: $($hermesExe.FullName)"
        } -ErrorAction Stop | Write-Output
        return $true
    } catch {
        Write-Warning "Hermes base verification failed: $($_.Exception.Message)"
        return $false
    }
}

# ---- 6. Copy Scripts and Files to VM ----
Write-Output "Preparing local codebase archive..."
$WorkspaceDir = (Get-Item $PSScriptRoot).Parent.FullName
$TempZipPath = Join-Path $env:TEMP "wright-local.zip"
if (Test-Path $TempZipPath) { Remove-Item $TempZipPath -Force }

# Create an archive of the wright repository on the host excluding heavy folders
Push-Location $WorkspaceDir
tar -cf $TempZipPath `
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

Write-Output "Copying files to VM..."
$LocalScript = Join-Path $PSScriptRoot "provision-vm.ps1"
$GuestScriptPath = "C:\Users\Public\Downloads\provision-vm.ps1"
$GuestZipPath = "C:\Users\Public\Downloads\wright.zip"

try {
    # Copy provisioning script
    Copy-VMFile -VMName $VmName -SourcePath $LocalScript -DestinationPath $GuestScriptPath -CreateFullPath -FileSource Host -Force
    
    # Copy repo archive
    Copy-VMFile -VMName $VmName -SourcePath $TempZipPath -DestinationPath $GuestZipPath -CreateFullPath -FileSource Host -Force
    
    Write-Output "Files successfully copied to the VM."
    Remove-Item $TempZipPath -Force -ErrorAction SilentlyContinue
} catch {
    Write-Error "ERROR: Failed to copy files to the VM. $_"
    Remove-Item $TempZipPath -Force -ErrorAction SilentlyContinue
    Exit 1
}

# ---- 7. Run Provisioning inside VM ----
if (-not $hasToolsCheckpoint -and -not $HermesAlreadyInstalled) {
    # Full first-time provisioning: install tools, then take tools-ready checkpoint
    Write-Output "Running full provisioning (tools + Wright + Hermes) inside the VM..."
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    Invoke-Command -VMName $VmName -Credential $cred -ScriptBlock {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        $ErrorActionPreference = "Continue"
        & C:\Users\Public\Downloads\provision-vm.ps1 -SkipWright -SkipDesktop
    } 2>&1 | ForEach-Object { Write-Output $_ }
    $ErrorActionPreference = $oldEAP
    Write-Output "Creating checkpoint 'tools-ready'..."
    Stop-VM -Name $VmName -Force
    Checkpoint-VM -Name $VmName -SnapshotName "tools-ready" | Out-Null
    Start-VM -Name $VmName
    Write-Output "'tools-ready' checkpoint saved. Continuing with Wright + Hermes install..."

    # Wait for VM to come back up after checkpoint
    $reconnected = $false
    for ($i = 1; $i -le 24; $i++) {
        try {
            Invoke-Command -VMName $VmName -Credential $cred -ScriptBlock { Get-Date } -ErrorAction Stop | Out-Null
            $reconnected = $true; break
        } catch { Start-Sleep -Seconds 5 }
    }
    if (-not $reconnected) { Write-Error "ERROR: VM did not come back after tools-ready checkpoint."; Exit 1 }
}

# Install and checkpoint the clean Hermes Desktop base before Wright is added.
if (-not $HermesAlreadyInstalled) {
    Write-Output "Installing latest Hermes Desktop and seeding API Server config inside the VM..."
    $hermesOk = $false
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        Write-Output "Hermes Desktop install attempt $attempt/2..."
        $oldEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            Invoke-Command -VMName $VmName -Credential $cred -ArgumentList $HermesSetupUrl -ScriptBlock {
                param($HermesSetupUrl)
                Set-ExecutionPolicy Bypass -Scope Process -Force
                $ErrorActionPreference = "Continue"
                & C:\Users\Public\Downloads\provision-vm.ps1 -SkipTools -SkipWright -HermesSetupUrl $HermesSetupUrl
            } 2>&1 | Tee-Object -Variable hermesOutput | ForEach-Object { Write-Output $_ }
        } catch {
            Write-Warning "Hermes install command ended early: $($_.Exception.Message)"
        } finally {
            $ErrorActionPreference = $oldEAP
        }

        if (-not (Wait-ForGuestPowerShell -VmName $VmName -Credential $cred -Attempts 40)) {
            Write-Warning "Guest did not become responsive after Hermes install attempt $attempt."
            continue
        }

        if (Test-GuestHermesBase -VmName $VmName -Credential $cred) {
            $hermesOk = $true
            break
        }

        Write-Warning "Hermes was not fully installed/configured after attempt $attempt."
    }

    if (-not $hermesOk) {
        Write-Error "ERROR: Hermes Desktop base install failed; not creating hermes-installed checkpoint."
        Exit 1
    }

    Write-Output "Creating checkpoint 'hermes-installed'..."
    Stop-VM -Name $VmName -Force
    Get-VMSnapshot -VMName $VmName -Name "hermes-installed" -ErrorAction SilentlyContinue |
        Remove-VMSnapshot -Confirm:$false -ErrorAction SilentlyContinue
    Checkpoint-VM -Name $VmName -SnapshotName "hermes-installed" | Out-Null
    Start-VM -Name $VmName
    Write-Output "'hermes-installed' checkpoint saved."

    if (-not (Wait-ForGuestPowerShell -VmName $VmName -Credential $cred -Attempts 40)) {
        Write-Error "ERROR: VM did not come back after hermes-installed checkpoint."
        Exit 1
    }
}

# Install Wright into the verified Hermes Desktop base.
Write-Output "Installing Wright/plugin into the Hermes Desktop VM..."
$oldEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
Invoke-Command -VMName $VmName -Credential $cred -ArgumentList $LlmApiUrl, $HermesSetupUrl -ScriptBlock {
    param($LlmApiUrl, $HermesSetupUrl)
    Set-ExecutionPolicy Bypass -Scope Process -Force
    $ErrorActionPreference = "Continue"
    & C:\Users\Public\Downloads\provision-vm.ps1 -SkipTools -SkipDesktop -LlmApiUrl $LlmApiUrl -HermesSetupUrl $HermesSetupUrl
} 2>&1 | Tee-Object -Variable provisionOutput | ForEach-Object { Write-Output $_ }
$ErrorActionPreference = $oldEAP
$provisionText = $provisionOutput | Out-String
if ($provisionText -match "ERROR:|WriteErrorException|Hermes CLI still reports") {
    Write-Error "ERROR: Guest provisioning failed; not creating ready-to-run checkpoint."
    Exit 1
}

# Save the fully-provisioned state
Write-Output "Creating checkpoint 'ready-to-run'..."
Stop-VM -Name $VmName -Force
Checkpoint-VM -Name $VmName -SnapshotName "ready-to-run" | Out-Null
Start-VM -Name $VmName
Write-Output "'ready-to-run' checkpoint saved."

# Wait for VM to come back
$reconnected2 = $false
for ($i = 1; $i -le 24; $i++) {
    try {
        Invoke-Command -VMName $VmName -Credential $cred -ScriptBlock { Get-Date } -ErrorAction Stop | Out-Null
        $reconnected2 = $true; break
    } catch { Start-Sleep -Seconds 5 }
}
if (-not $reconnected2) { Write-Error "ERROR: VM did not come back after ready-to-run checkpoint."; Exit 1 }

# ---- 8. Start Everything & Open GUI Console ----
Write-Output "Starting Wright backend and Hermes Desktop inside the VM..."

# Run the startup in the background of the guest VM
Invoke-Command -VMName $VmName -Credential $cred -AsJob -ArgumentList $LlmApiUrl, $HermesSetupUrl -ScriptBlock {
    param($LlmApiUrl, $HermesSetupUrl)
    Set-ExecutionPolicy Bypass -Scope Process -Force
    & C:\Users\Public\Downloads\provision-vm.ps1 -SkipTools -SkipWright -SkipDesktop -StartServers -LlmApiUrl $LlmApiUrl -HermesSetupUrl $HermesSetupUrl
} | Out-Null

if (-not $NoExpose) {
    Write-Output "Exposing Wright API from VM port $GuestPort on host http://${ListenAddress}:${HostPort}..."
    $ManageVmScript = Join-Path $PSScriptRoot "manage-vm.ps1"
    & $ManageVmScript expose -VmName $VmName -ListenAddress $ListenAddress -HostPort $HostPort -GuestPort $GuestPort
} else {
    Write-Output "Skipping host port forwarding because -NoExpose was specified."
}

Write-Output ""
Write-Output "=============================================================="
Write-Output "  Wright VM Environment Running!"
Write-Output "=============================================================="
if ($NoConnect) {
    Write-Output "  - VM Console was not opened. Run: .\manage-vm.ps1 connect"
} else {
    Write-Output "  - VM Console has been opened on your desktop."
}
Write-Output "  - The Wright backend is running inside the VM."
Write-Output "  - Hermes Desktop is launching inside the VM."
if (-not $NoExpose) {
    Write-Output "  - Host API endpoint: http://${ListenAddress}:${HostPort}"
}
Write-Output "=============================================================="
Write-Output ""
