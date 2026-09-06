# Building AI-Base Linux

## Prerequisites (Arch Linux host only)

```bash
sudo pacman -S --needed archiso calamares qemu-desktop edk2-ovmf base-devel imagemagick
```

Windows/macOS are not supported build hosts — use an Arch Linux VM or WSL2
Arch distro.

### Setting up a build VM on Windows (Hyper-V + Omarchy)

If you don't have an Arch Linux machine yet, `scripts/windows/setup-omarchy-vm.ps1`
automates creating a Hyper-V VM (Secure Boot off, nested virtualization on)
and downloading the [Omarchy](https://omarchy.org/) ISO — Omarchy is Arch
Linux underneath, so it works fine as a build host. Run it from an
**elevated** PowerShell prompt:

```powershell
./scripts/windows/setup-omarchy-vm.ps1
```

The OS install itself is interactive (disk pick + LUKS passphrase) since
Omarchy has no unattended install mode — the script prints the remaining
manual steps once the VM console opens.

**Windows Home has no Hyper-V** (`Enable-WindowsOptionalFeature` errors with
"Feature name Microsoft-Hyper-V-All is unknown" — the feature isn't just
disabled, it's absent). Use `scripts/windows/setup-omarchy-vm-virtualbox.ps1`
instead — same idea, built on `VBoxManage` (no elevation needed, only
requires VirtualBox to already be installed, e.g. `winget install
Oracle.VirtualBox`):

```powershell
./scripts/windows/setup-omarchy-vm-virtualbox.ps1
```

VirtualBox's nested virtualization support is less reliable than Hyper-V's,
so QEMU testing *inside* this VM may fall back to slow software emulation —
still fine for a basic ISO-boot smoke test.

## Build steps

```bash
git clone <this repo>
cd custom-linux-distro
./scripts/build-iso.sh
```

This runs, in order:
1. `scripts/generate-branding-placeholders.sh` — generates simple placeholder
   logo/welcome/tray-icon PNGs with ImageMagick if they don't exist yet, so
   Calamares and the desktop don't show broken images before real artwork
   is designed. Safe to re-run; set `FORCE=1` to regenerate.
2. `scripts/build-local-repo.sh` — builds the `ai-assistant` pacman package
   (via `ai-assistant/packaging/PKGBUILD`) into a local repo at
   `/tmp/aibase-local-repo`, referenced by `airootfs-profile/pacman.conf`.
3. `scripts/enable-services.sh` — creates the systemd `.wants` symlinks
   (NetworkManager, lightdm, the first-boot units) inside
   `airootfs-profile/airootfs/`. Done as a script rather than committed
   symlinks because they don't survive a Windows checkout reliably.
4. `mkarchiso` — builds the ISO into `out/`.

Test it:

```bash
./scripts/test-iso-qemu.sh
```

## What happens on first boot of the *installed* system

- `aibase-plymouth-setup.service` (oneshot, runs first) adds the `plymouth`
  mkinitcpio hook if Calamares' own initcpiocfg didn't include it, activates
  the `aibase` boot theme, and regenerates the initramfs. See
  [airootfs/usr/local/bin/aibase-plymouth-setup](../airootfs-profile/airootfs/usr/local/bin/aibase-plymouth-setup).
- `aibase-gpu-detect.service` (oneshot) detects NVIDIA vs integrated GPU via
  `lspci` and blacklists/removes the unused driver stack, then disables
  itself. If `nvidia-open` fails to bind to the card (older, pre-Turing
  GPUs), it automatically downloads the proprietary `nvidia` package instead
  - requires internet on first boot for that fallback path only. See
  [airootfs/usr/local/bin/aibase-gpu-detect](../airootfs-profile/airootfs/usr/local/bin/aibase-gpu-detect).
- `aibase-first-boot-setup.service` (oneshot) enables `ollama.service` and
  pulls a default model sized to the machine's RAM (3B model under 15GB RAM,
  8B model otherwise). Requires internet on first boot — if it's not
  available, the assistant's Model Manager lets the user pull a model later.
  See [airootfs/usr/local/bin/aibase-first-boot-setup](../airootfs-profile/airootfs/usr/local/bin/aibase-first-boot-setup).

## Known gaps / TODO before a public release

- **Branding images are auto-generated placeholders.**
  `scripts/generate-branding-placeholders.sh` creates simple solid-color
  logo/welcome/tray-icon/Plymouth-splash PNGs so nothing shows a broken
  image or blank boot screen, but the placeholders should be replaced with
  real artwork (`FORCE=1 ./scripts/generate-branding-placeholders.sh` to
  regenerate) before a public release.
- **No model is bundled in the ISO.** The default model is downloaded on
  first boot instead (see above), because bundling a multi-GB model binary
  in this scaffold isn't practical here. If guaranteed offline-out-of-the-box
  behavior is required, add the `.gguf`/Ollama blob to
  `airootfs-profile/airootfs/var/lib/ollama/` at build time and skip the
  first-boot pull step.
- **Local repo package versioning**: `PKGBUILD` builds from the local
  checkout directly; wire up CI or a release tarball before publishing.
- **NVIDIA fallback is untested on real hardware** - the `modprobe`/`nvidia-smi`
  success check in `aibase-gpu-detect` is a reasonable heuristic but should
  be verified on an actual pre-Turing GPU before relying on it.
- **Plymouth hook insertion is a heuristic.** `aibase-plymouth-setup`'s `sed`
  assumes `HOOKS=(...udev...)` appears on a single line as Calamares'
  initcpiocfg module typically writes it; if that module produces a
  different format the hook insertion silently no-ops (theme just won't
  show, boot still works) - verify on a real Calamares install.
