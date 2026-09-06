# AI-Base Linux (working name)

A custom Arch Linux respin with XFCE, a Calamares GUI installer (no terminal
required to install), and a built-in local AI assistant powered by
[Ollama](https://ollama.com/) — works fully offline once installed, and
auto-detects NVIDIA vs integrated GPUs.

## Project layout

```
airootfs-profile/     archiso live-build profile (base for the ISO)
calamares-config/      Calamares installer module/branding configuration
ai-assistant/           Local AI assistant tray app (Python/GTK) + PKGBUILD + tests
scripts/                Build helpers and first-boot setup scripts
docs/                   Build and architecture documentation
.github/workflows/      CI: Python syntax/tests, shellcheck, yamllint
```

## Requirements to build

This must be built on an **Arch Linux machine** (or Arch container/VM) with:
`archiso`, `calamares`, `qemu-desktop`, `edk2-ovmf`, `imagemagick` installed.
Windows is not a supported build host — use WSL2 with an Arch Linux distro,
or a VM.

## Quick start (on Arch Linux)

```bash
./scripts/build-iso.sh
./scripts/test-iso-qemu.sh   # boots the produced ISO in QEMU
```

See [docs/BUILDING.md](docs/BUILDING.md) for full details and
[docs/AI-ASSISTANT.md](docs/AI-ASSISTANT.md) for the assistant's architecture.

## Running the assistant's unit tests (works on any OS with Python)

```bash
cd ai-assistant
pip install -e .[test]
pytest -q
```

## Status

Scaffold complete and unit-tested where possible without a Linux host (see
`docs/BUILDING.md` for the "Known gaps" list) — the ISO build itself, GPU
driver fallback, Plymouth theme, and GTK UI still need verification on a
real Arch Linux machine.
