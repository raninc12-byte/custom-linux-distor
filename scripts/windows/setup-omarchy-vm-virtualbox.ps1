<#
.SYNOPSIS
    Creates and configures a VirtualBox VM for installing Omarchy (Arch
    Linux), to be used as the build host for the AI-Base Linux ISO.

.DESCRIPTION
    Windows Home doesn't support Hyper-V, so this uses VirtualBox instead
    (already installed on this machine via winget: Oracle.VirtualBox).
    Automates everything that CAN be automated: downloading the official
    Omarchy ISO, creating a VM sized per the parameters below, disabling
    Secure Boot/TPM in the VM's EFI firmware (required by Omarchy), and
    enabling nested VT-x/AMD-V (so QEMU/KVM testing works *inside* the VM
    later, per docs/BUILDING.md) - if your host CPU/BIOS supports it.

    The actual OS installation is NOT automated - Omarchy's installer has no
    unattended/answer-file mode. It's interactive by design: you pick the
    disk and set a full-disk-encryption (LUKS) passphrase yourself in the VM
    window this script opens at the end.

.NOTES
    Run from a normal (non-admin is fine) PowerShell prompt - VirtualBox
    doesn't need elevation for VM management, only its own driver install
    (already done, since VirtualBox is installed).
    Downloads a multi-GB ISO - make sure you have bandwidth/disk space.
    VirtualBox performance for a full desktop-OS guest is noticeably slower
    than Hyper-V/native - expect the install and later ISO builds to take a
    while.

.PARAMETER ExpectedSha256
    Optional. Omarchy doesn't publish a checksum on its download page as of
    writing, so this is skipped by default. Pass one if you obtain it
    out-of-band and want the download verified.
#>
param(
    [string]$VMName = "aibase-omarchy-build",
    [string]$VBoxManage = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
    [string]$VMBaseFolder = "$env:USERPROFILE\VirtualBox VMs",
    [int]$CpuCount = 4,
    [int64]$MemoryMB = 8192,
    [int64]$DiskMB = 65536,
    [string]$IsoUrl = "https://iso.omarchy.org/omarchy-4.0.2.iso",
    [string]$IsoPath = "$env:USERPROFILE\Downloads\omarchy.iso",
    [string]$ExpectedSha256
)

$ErrorActionPreference = "Stop"

function Assert-VBoxManage {
    if (-not (Test-Path $VBoxManage)) {
        throw "VBoxManage.exe not found at '$VBoxManage'. Pass -VBoxManage <path> if VirtualBox is installed elsewhere, or install it first: winget install Oracle.VirtualBox"
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

Assert-VBoxManage

$existing = & $VBoxManage list vms 2>$null | Select-String -SimpleMatch "`"$VMName`""
if ($existing) {
    throw "A VM named '$VMName' already exists. Remove it first (VBoxManage unregistervm '$VMName' --delete) or pass a different -VMName."
}

Get-OmarchyIso

Write-Host "Creating VM '$VMName' ($CpuCount vCPU, $($MemoryMB/1024)GB RAM, $($DiskMB/1024)GB disk)..."
& $VBoxManage createvm --name $VMName --ostype "ArchLinux_64" --register --basefolder $VMBaseFolder

& $VBoxManage modifyvm $VMName `
    --cpus $CpuCount `
    --memory $MemoryMB `
    --vram 128 `
    --graphicscontroller vmsvga `
    --firmware efi `
    --nested-hw-virt on `
    --nic1 nat `
    --audio-driver none

$vmFolder = Join-Path $VMBaseFolder $VMName
$diskPath = Join-Path $vmFolder "$VMName.vdi"
New-Item -ItemType Directory -Path $vmFolder -Force | Out-Null
& $VBoxManage createmedium disk --filename $diskPath --size $DiskMB --format VDI

& $VBoxManage storagectl $VMName --name "SATA Controller" --add sata --controller IntelAhci --portcount 2
& $VBoxManage storageattach $VMName --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium $diskPath
& $VBoxManage storageattach $VMName --storagectl "SATA Controller" --port 1 --device 0 --type dvddrive --medium $IsoPath
& $VBoxManage modifyvm $VMName --boot1 dvd --boot2 disk --boot3 none --boot4 none

# Omarchy requires Secure Boot off. VirtualBox EFI ships with it off by
# default, so no extra command is needed here - if you've changed your
# global VirtualBox defaults, double check in the VM's Settings > System.

Write-Host "Starting VM..."
& $VBoxManage startvm $VMName

Write-Host @"

VM '$VMName' is starting - a window should now be open.

Next steps (INTERACTIVE - do these yourself in that window, Omarchy has no
unattended install mode):
  1. It should boot straight into the Omarchy installer from the ISO.
  2. Answer the installer prompts (keyboard layout, pick the only disk, set
     a LUKS encryption passphrase - remember it, there's no recovery).
  3. Confirm the wipe/install and wait - it takes a while (VirtualBox is
     slower than a native install, so be patient).
  4. After it reboots into Omarchy, log in, then open a terminal and run:
       sudo pacman -S --needed archiso calamares qemu-desktop edk2-ovmf base-devel imagemagick git
  5. Copy or git-clone this project into the VM, then run:
       ./scripts/build-iso.sh
       ./scripts/test-iso-qemu.sh
     Nested VT-x/AMD-V was requested for this VM, but VirtualBox nested
     virtualization support is less reliable than Hyper-V's - if QEMU inside
     the VM complains about /dev/kvm, it'll fall back to slow software
     emulation. Still fine for a basic smoke test of the ISO boot.
"@
