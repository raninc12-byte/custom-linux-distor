<#
.SYNOPSIS
    Creates and configures a Hyper-V VM for installing Omarchy (Arch Linux),
    to be used as the build host for the AI-Base Linux ISO.

.DESCRIPTION
    Automates everything that CAN be automated: Hyper-V checks, downloading
    the official Omarchy ISO, creating a Generation 2 VM sized per the
    parameters below, disabling Secure Boot (required by Omarchy), and
    enabling nested virtualization (so QEMU/KVM testing works *inside* the
    VM later, per docs/BUILDING.md).

    The actual OS installation is NOT automated - Omarchy's installer has no
    unattended/answer-file mode. It's interactive by design: you pick the
    disk and set a full-disk-encryption (LUKS) passphrase yourself in the VM
    Connect window this script opens at the end.

.NOTES
    Run from an ELEVATED (Administrator) PowerShell prompt. Requires
    Windows Pro/Enterprise/Education (Hyper-V isn't available on Home).
    Downloads a multi-GB ISO - make sure you have bandwidth/disk space.

.PARAMETER ExpectedSha256
    Optional. Omarchy doesn't publish a checksum on its download page as of
    writing, so this is skipped by default. Pass one if you obtain it
    out-of-band and want the download verified.
#>
param(
    [string]$VMName = "aibase-omarchy-build",
    [string]$VMPath = "$env:USERPROFILE\HyperV\$VMName",
    [int]$CpuCount = 4,
    [int64]$MemoryGB = 8,
    [int64]$DiskGB = 64,
    [string]$IsoUrl = "https://iso.omarchy.org/omarchy-4.0.2.iso",
    [string]$IsoPath = "$env:USERPROFILE\Downloads\omarchy.iso",
    [string]$SwitchName,
    [string]$ExpectedSha256
)

$ErrorActionPreference = "Stop"

function Assert-Admin {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from an elevated (Administrator) PowerShell prompt."
    }
}

function Assert-HyperV {
    $feature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -ErrorAction SilentlyContinue
    if (-not $feature -or $feature.State -ne "Enabled") {
        throw "Hyper-V isn't enabled. Run (as admin), reboot, then re-run this script:`n" +
              "  Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All`n" +
              "(Requires Windows Pro/Enterprise/Education - not available on Home.)"
    }
}

function Get-OmarchyIso {
    if (Test-Path $IsoPath) {
        Write-Host "Reusing existing ISO at $IsoPath"
    } else {
        Write-Host "Downloading Omarchy ISO from $IsoUrl ..."
        Write-Host "(Multi-GB download - this will take a while.)"
        Invoke-WebRequest -Uri $IsoUrl -OutFile $IsoPath
    }

    if ($ExpectedSha256) {
        $actual = (Get-FileHash -Path $IsoPath -Algorithm SHA256).Hash
        if ($actual -ne $ExpectedSha256.ToUpper()) {
            throw "SHA256 mismatch for $IsoPath`nExpected: $ExpectedSha256`nActual:   $actual"
        }
        Write-Host "SHA256 verified."
    } else {
        Write-Host "No -ExpectedSha256 given (Omarchy doesn't publish one) - skipping verification."
    }
}

function Resolve-VMSwitch {
    if ($SwitchName) {
        if (-not (Get-VMSwitch -Name $SwitchName -ErrorAction SilentlyContinue)) {
            throw "VMSwitch '$SwitchName' does not exist. Create it first or omit -SwitchName to auto-create one."
        }
        return $SwitchName
    }

    $existing = Get-VMSwitch | Select-Object -First 1
    if ($existing) {
        Write-Host "Using existing virtual switch: $($existing.Name)"
        return $existing.Name
    }

    $newName = "aibase-external-switch"
    $adapter = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object -First 1
    if (-not $adapter) {
        throw "No active network adapter found to bind an external switch to. Create a VMSwitch manually and pass -SwitchName."
    }
    Write-Host "Creating external virtual switch '$newName' bound to $($adapter.Name)..."
    New-VMSwitch -Name $newName -NetAdapterName $adapter.Name -AllowManagementOS $true | Out-Null
    return $newName
}

Assert-Admin
Assert-HyperV

if (Get-VM -Name $VMName -ErrorAction SilentlyContinue) {
    throw "A VM named '$VMName' already exists. Remove it first (Remove-VM) or pass a different -VMName."
}

Get-OmarchyIso
$switch = Resolve-VMSwitch

New-Item -ItemType Directory -Path $VMPath -Force | Out-Null
$vhdPath = Join-Path $VMPath "$VMName.vhdx"

Write-Host "Creating VM '$VMName' ($CpuCount vCPU, ${MemoryGB}GB RAM, ${DiskGB}GB disk)..."
New-VM -Name $VMName -Generation 2 -MemoryStartupBytes ($MemoryGB * 1GB) `
    -NewVHDPath $vhdPath -NewVHDSizeBytes ($DiskGB * 1GB) -SwitchName $switch -Path $VMPath | Out-Null

Set-VMProcessor -VMName $VMName -Count $CpuCount -ExposeVirtualizationExtensions $true
Add-VMDvdDrive -VMName $VMName -Path $IsoPath
$dvd = Get-VMDvdDrive -VMName $VMName
Set-VMFirmware -VMName $VMName -EnableSecureBoot Off -FirstBootDevice $dvd

Write-Host "Starting VM and opening console..."
Start-VM -Name $VMName
Start-Process "vmconnect.exe" -ArgumentList "localhost", $VMName

Write-Host @"

VM '$VMName' is running - a console window should now be open.

Next steps (INTERACTIVE - do these yourself in that window, Omarchy has no
unattended install mode):
  1. It should boot straight into the Omarchy installer from the ISO.
     Secure Boot is already off on this VM, so no firmware changes needed.
  2. Answer the installer prompts (keyboard layout, pick the only disk, set
     a LUKS encryption passphrase - remember it, there's no recovery).
  3. Confirm the wipe/install and wait - it takes a while.
  4. After it reboots into Omarchy, log in, then open a terminal and run:
       sudo pacman -S --needed archiso calamares qemu-desktop edk2-ovmf base-devel imagemagick git
  5. Copy or git-clone this project into the VM, then run:
       ./scripts/build-iso.sh
       ./scripts/test-iso-qemu.sh
     (nested virtualization is enabled on this VM, so QEMU inside it should
     get real acceleration instead of falling back to slow software emulation)
"@
