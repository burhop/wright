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
    [switch]$SkipDownload
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
$hasReadyCheckpoint = $false
if ($VnExists) {
    $hasToolsCheckpoint = $null -ne (Get-VMSnapshot -VMName $VmName -Name "tools-ready" -ErrorAction SilentlyContinue)
    $hasReadyCheckpoint  = $null -ne (Get-VMSnapshot -VMName $VmName -Name "ready-to-run" -ErrorAction SilentlyContinue)
}

# If VM exists and has at least the tools-ready checkpoint, revert to it and
# reinstall only Wright + Hermes (fast path for testing new versions)
if ($VnExists -and $hasToolsCheckpoint) {
    Write-Output "VM '$VmName' found. Reverting to 'tools-ready' checkpoint for a clean Wright install..."
    Stop-VM -Name $VmName -Force -ErrorAction SilentlyContinue
    # Remove old ready-to-run checkpoint so we can create a fresh one
    if ($hasReadyCheckpoint) {
        Remove-VMSnapshot -VMName $VmName -Name "ready-to-run" -ErrorAction SilentlyContinue
    }
    Restore-VMSnapshot -VMName $VmName -Name "tools-ready" -Confirm:$false
    Start-VM -Name $VmName
    Write-Output "Reverted to 'tools-ready'. Continuing with Wright + Hermes setup..."
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

# Open VM Connection console immediately so the user can see the boot process
Write-Output "Opening VM Connection Console so you can monitor the boot process..."
Start-Process vmconnect.exe -ArgumentList "localhost", $VmName -ErrorAction SilentlyContinue

# ---- 5. Establish PowerShell Direct Connection ----
Write-Output "Establishing connection to VM guest OS (using default credentials)..."
$password = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("User", $password)

Write-Output "Waiting for Windows guest OS to boot and become responsive..."
$connected = $false
$currentCred = $cred
for ($i = 1; $i -le 40; $i++) {
    try {
        # Check connection via PowerShell Direct (which doesn't require network)
        Invoke-Command -VMName $VmName -Credential $currentCred -ScriptBlock { Get-Date } -ErrorAction Stop | Out-Null
        $connected = $true
        $cred = $currentCred # Save the working credentials to be used by subsequent steps
        break
    } catch {
        $err = $_.Exception.Message
        if ($err -like "*credential*") {
            Write-Output ""
            Write-Warning "The connection credentials were rejected by the VM."
            Write-Output "Please provide the username and password of the account you logged into inside the VM."
            $user = Read-Host "Username (default: User)"
            if ([string]::IsNullOrEmpty($user)) { $user = "User" }
            $passStr = Read-Host -AsSecureString "Password"
            $currentCred = New-Object System.Management.Automation.PSCredential ($user, $passStr)
            Write-Output "Retrying connection with new credentials..."
        } else {
            Write-Output "  Waiting for boot (attempt $i/40)... [Diagnostic: $err]"
            Start-Sleep -Seconds 5
        }
    }
}

if (-not $connected) {
    Write-Error "ERROR: VM did not become responsive to PowerShell Direct within the timeout period."
    Write-Output "Please open Hyper-V Manager, connect to the VM, and verify it booted correctly."
    Exit 1
}
Write-Output "Connection established successfully!"

# ---- 6. Copy Scripts and Files to VM ----
Write-Output "Preparing local codebase archive..."
$WorkspaceDir = (Get-Item $PSScriptRoot).Parent.FullName
$TempZipPath = Join-Path $env:TEMP "wright-local.zip"
if (Test-Path $TempZipPath) { Remove-Item $TempZipPath -Force }

# Create an archive of the wright repository on the host excluding heavy folders
Push-Location $WorkspaceDir
tar -cf $TempZipPath --exclude="node_modules" --exclude=".venv" --exclude=".git" --exclude="windows-sandbox/.vm" .
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
if (-not $hasToolsCheckpoint) {
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

# Install Wright + Hermes (runs on first-time setup AND on version update runs)
Write-Output "Installing Wright + Hermes Desktop inside the VM..."
$oldEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
Invoke-Command -VMName $VmName -Credential $cred -ScriptBlock {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    $ErrorActionPreference = "Continue"
    & C:\Users\Public\Downloads\provision-vm.ps1 -SkipTools
} 2>&1 | ForEach-Object { Write-Output $_ }
$ErrorActionPreference = $oldEAP

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
Invoke-Command -VMName $VmName -Credential $cred -AsJob -ScriptBlock {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    & C:\Users\Public\Downloads\provision-vm.ps1 -SkipTools -SkipWright -SkipDesktop -StartServers
} | Out-Null



Write-Output ""
Write-Output "=============================================================="
Write-Output "  Wright VM Environment Running!"
Write-Output "=============================================================="
Write-Output "  - VM Console has been opened on your desktop."
Write-Output "  - The Wright backend is running inside the VM."
Write-Output "  - Hermes Desktop is launching inside the VM."
Write-Output "=============================================================="
Write-Output ""
