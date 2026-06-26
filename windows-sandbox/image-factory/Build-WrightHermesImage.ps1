param(
    [Parameter(Mandatory=$true)]
    [string]$WindowsIsoPath,

    [Parameter(Mandatory=$true)]
    [string]$WindowsIsoChecksum,

    [string]$GuestUsername = "wrightadmin",

    [Parameter(Mandatory=$true)]
    [string]$GuestPassword,

    [string]$HermesSetupUrl = "https://hermes-assets.nousresearch.com/Hermes-Setup.exe",
    [string]$HermesSetupArguments = "/S",
    [int]$HermesInstallTimeoutSeconds = 600,
    [string]$SwitchName = "Default Switch",
    [string]$VmName = "wright-hermes-image-build",
    [switch]$SkipNoPromptIso,
    [string]$NoPromptIsoPath,
    [string]$OutputRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) ".vm\image-factory")
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from an Administrator PowerShell on the Hyper-V host."
    }
}

function Resolve-RequiredCommand {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Name,

        [string]$WingetPackagePattern
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    if ($WingetPackagePattern) {
        $wingetRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
        if (Test-Path $wingetRoot) {
            $candidate = Get-ChildItem -Path $wingetRoot -Recurse -Filter $Name -ErrorAction SilentlyContinue |
                Where-Object { $_.FullName -like "*$WingetPackagePattern*" } |
                Select-Object -First 1
            if ($candidate) {
                $env:Path = "$($candidate.DirectoryName);$env:Path"
                return $candidate.FullName
            }
        }
    }

    throw "$Name was not found on PATH."
}

function New-NoPromptWindowsIso {
    param(
        [Parameter(Mandatory=$true)]
        [string]$SourceIsoPath,

        [Parameter(Mandatory=$true)]
        [string]$DestinationIsoPath,

        [Parameter(Mandatory=$true)]
        [string]$OscdimgPath
    )

    $destination = New-Item -ItemType Directory -Path (Split-Path -Parent $DestinationIsoPath) -Force
    $resolvedDestination = Join-Path $destination.FullName (Split-Path -Leaf $DestinationIsoPath)

    if ((Test-Path $resolvedDestination) -and
        ((Get-Item $resolvedDestination).LastWriteTimeUtc -ge (Get-Item $SourceIsoPath).LastWriteTimeUtc)) {
        return (Resolve-Path $resolvedDestination).Path
    }

    $mounted = $false
    try {
        $image = Mount-DiskImage -ImagePath $SourceIsoPath -PassThru
        $mounted = $true
        $volume = $image | Get-Volume | Select-Object -First 1
        if (-not $volume -or -not $volume.DriveLetter) {
            throw "Mounted ISO has no drive letter: $SourceIsoPath"
        }

        $sourceRoot = "$($volume.DriveLetter):\"
        $biosBoot = Join-Path $sourceRoot "boot\etfsboot.com"
        $efiBoot = Join-Path $sourceRoot "efi\microsoft\boot\efisys_noprompt.bin"
        if (-not (Test-Path $biosBoot)) {
            throw "Windows ISO is missing BIOS boot image: $biosBoot"
        }
        if (-not (Test-Path $efiBoot)) {
            throw "Windows ISO is missing UEFI no-prompt boot image: $efiBoot"
        }

        if (Test-Path $resolvedDestination) {
            Remove-Item -Path $resolvedDestination -Force
        }

        $oscdimgOutput = & $OscdimgPath `
            -m `
            -o `
            -u2 `
            -udfver102 `
            "-bootdata:2#p0,e,b$biosBoot#pEF,e,b$efiBoot" `
            $sourceRoot `
            $resolvedDestination `
            2>&1
        if ($LASTEXITCODE -ne 0) {
            $oscdimgOutput | ForEach-Object { Write-Host $_ }
            throw "oscdimg failed with exit code $LASTEXITCODE."
        }
        $oscdimgOutput | ForEach-Object { Write-Host $_ }
    } finally {
        if ($mounted) {
            Dismount-DiskImage -ImagePath $SourceIsoPath | Out-Null
        }
    }

    return (Resolve-Path $resolvedDestination).Path
}

Assert-Administrator

$packerPath = Resolve-RequiredCommand -Name "packer.exe" -WingetPackagePattern "Hashicorp.Packer"
if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
    throw "Hyper-V PowerShell cmdlets are not available."
}
if (-not (Test-Path $WindowsIsoPath)) {
    throw "Windows ISO was not found: $WindowsIsoPath"
}

$factoryRoot = New-Item -ItemType Directory -Path $OutputRoot -Force
$generatedRoot = New-Item -ItemType Directory -Path (Join-Path $factoryRoot.FullName "generated") -Force
$publishedRoot = New-Item -ItemType Directory -Path (Join-Path $factoryRoot.FullName "published") -Force
$buildOutput = Join-Path $factoryRoot.FullName "packer-output"
$effectiveIsoPath = (Resolve-Path $WindowsIsoPath).Path
$effectiveIsoChecksum = $WindowsIsoChecksum

if (-not $SkipNoPromptIso) {
    $oscdimgPath = Resolve-RequiredCommand -Name "oscdimg.exe" -WingetPackagePattern "Microsoft.OSCDIMG"
    if (-not $NoPromptIsoPath) {
        $sourceIso = Get-Item $effectiveIsoPath
        $NoPromptIsoPath = Join-Path $sourceIso.DirectoryName ($sourceIso.BaseName + ".noprompt.iso")
    }

    Write-Output "Preparing no-prompt Windows boot ISO..."
    $effectiveIsoPath = New-NoPromptWindowsIso `
        -SourceIsoPath $effectiveIsoPath `
        -DestinationIsoPath $NoPromptIsoPath `
        -OscdimgPath $oscdimgPath
    $effectiveIsoChecksum = "sha256:$((Get-FileHash -Path $effectiveIsoPath -Algorithm SHA256).Hash)"
    Write-Output "  ISO:      $effectiveIsoPath"
    Write-Output "  Checksum: $effectiveIsoChecksum"
}

if (Test-Path $buildOutput) {
    Remove-Item -Path $buildOutput -Recurse -Force
}

$templatePath = Join-Path $PSScriptRoot "packer\autounattend\Autounattend.xml.template"
$autounattendPath = Join-Path $generatedRoot.FullName "Autounattend.xml"
$autounattend = Get-Content -Path $templatePath -Raw
$autounattend = $autounattend.Replace("{{GUEST_USERNAME}}", [Security.SecurityElement]::Escape($GuestUsername))
$autounattend = $autounattend.Replace("{{GUEST_PASSWORD}}", [Security.SecurityElement]::Escape($GuestPassword))
Set-Content -Path $autounattendPath -Value $autounattend -Encoding UTF8

$packerDir = Join-Path $PSScriptRoot "packer"
Push-Location $packerDir
try {
    & $packerPath init .
    & $packerPath validate `
        -var "iso_url=$effectiveIsoPath" `
        -var "iso_checksum=$effectiveIsoChecksum" `
        -var "autounattend_path=$autounattendPath" `
        -var "guest_username=$GuestUsername" `
        -var "guest_password=$GuestPassword" `
        -var "hermes_setup_url=$HermesSetupUrl" `
        -var "hermes_setup_arguments=$HermesSetupArguments" `
        -var "hermes_install_timeout_seconds=$HermesInstallTimeoutSeconds" `
        -var "output_directory=$buildOutput" `
        -var "switch_name=$SwitchName" `
        -var "vm_name=$VmName" `
        .
    & $packerPath build -force `
        -var "iso_url=$effectiveIsoPath" `
        -var "iso_checksum=$effectiveIsoChecksum" `
        -var "autounattend_path=$autounattendPath" `
        -var "guest_username=$GuestUsername" `
        -var "guest_password=$GuestPassword" `
        -var "hermes_setup_url=$HermesSetupUrl" `
        -var "hermes_setup_arguments=$HermesSetupArguments" `
        -var "hermes_install_timeout_seconds=$HermesInstallTimeoutSeconds" `
        -var "output_directory=$buildOutput" `
        -var "switch_name=$SwitchName" `
        -var "vm_name=$VmName" `
        .
} finally {
    Pop-Location
}

$vhdx = Get-ChildItem -Path $buildOutput -Filter "*.vhdx" -Recurse | Select-Object -First 1
if (-not $vhdx) {
    throw "Packer completed but no VHDX was found under $buildOutput."
}

$publishedPath = Join-Path $publishedRoot.FullName "wright-hermes-ready.vhdx"
Copy-Item -Path $vhdx.FullName -Destination $publishedPath -Force

$manifest = [ordered]@{
    artifact          = $publishedPath
    source_iso        = (Resolve-Path $WindowsIsoPath).Path
    source_checksum   = $WindowsIsoChecksum
    build_iso         = $effectiveIsoPath
    build_checksum    = $effectiveIsoChecksum
    guest_username    = $GuestUsername
    hermes_setup_url  = $HermesSetupUrl
    hermes_setup_args = $HermesSetupArguments
    created_utc       = (Get-Date).ToUniversalTime().ToString("o")
    builder           = "packer hyperv-iso"
}
$manifestPath = Join-Path $publishedRoot.FullName "wright-hermes-ready.manifest.json"
$manifest | ConvertTo-Json | Set-Content -Path $manifestPath -Encoding UTF8

Write-Output ""
Write-Output "Published Hermes-ready image:"
Write-Output "  VHDX:     $publishedPath"
Write-Output "  Manifest: $manifestPath"
