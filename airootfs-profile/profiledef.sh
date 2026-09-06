#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="aibase-linux"
iso_label="AIBASE_$(date +%Y%m)"
iso_publisher="AI-Base Linux <https://example.invalid>"
iso_application="AI-Base Linux Live/Install medium"
iso_version="$(date +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito'
           'uefi-ia32.grub.esp' 'uefi-x64.grub.esp'
           'uefi-ia32.grub.eltorito' 'uefi-x64.grub.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '19')
bootstrap_tarball_compression=('zstd' '-c' '-T0' '--long' '-19')
file_permissions=(
  ["/etc/shadow"]="0:0:0400"
  ["/etc/gshadow"]="0:0:0400"
  ["/root"]="0:0:0750"
  ["/usr/local/bin/aibase-gpu-detect"]="0:0:0755"
  ["/usr/local/bin/aibase-first-boot-setup"]="0:0:0755"
  ["/usr/local/bin/aibase-plymouth-setup"]="0:0:0755"
)
