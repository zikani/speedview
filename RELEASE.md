# SpeedView Release & Auto-Updater Guide

This document explains how SpeedView packages cross-platform installers (`Program Files\SpeedView` `onedir` layout + GUI `.msi` / `SpeedView-Setup.exe`) and how the built-in background auto-updater downloads, stages, swaps, and restarts updates across Windows, macOS, and Linux.

---

## How the Auto-Updater Works

Because an active desktop application cannot reliably overwrite its own open binary or shared `_internal/` libraries while running, SpeedView uses an **`onedir` `Program Files\SpeedView` layout + 3-day rate-limited GitHub Releases check + temp `.zip` staging + detached Python subprocess swap-and-restart** flow (`speedview/update/updater.py`).

### Why Extracted `Program Files\SpeedView` (`onedir`) Replaces Standalone `.exe`
- **No manual download-and-delete step**: Replacing `C:\Program Files\SpeedView\` (both `SpeedView.exe` and `_internal\`) updates the existing installation cleanly in place.
- **MSI + GUI Installer/Uninstaller**: Users install once with `SpeedView-windows-x64.msi` or `SpeedView-Setup.exe`, get Desktop and Start Menu shortcuts plus `SpeedView.ico` file/taskbar icons, and uninstall cleanly from Windows **Apps & Features**.

### End-to-End Update Flow

```text
App Startup / 6h Timer
   │
   ▼  (Is auto_update=true AND >= 3 days since last_update_check?)
GitHub Releases API (/releases/latest + /releases?per_page=30)
   │
   ├──► Caches release changelogs & features in releases_cache.json
   │    (About & Update dialogs always list ALL released versions)
   │
   ▼  (Newer semver tag found? Pick OS-matching onedir .zip asset)
Download .zip ──► Temp Staging Folder (speedview_update_*)
   │
   ▼  (Safe ZipSlip-checked extraction + POSIX chmod preservation)
Launch Detached Python Updater Subprocess (UAC elevated if Program Files)
   │
   ▼
Main App Exits (force_quit)
   │
   ├──► Helper waits for PID exit
   ├──► Copies extracted onedir folder (SpeedView.exe + _internal/) into Program Files\SpeedView
   ├──► Removes temporary staging directory
   ├──► Restarts updated SpeedView binary / .app
   └──► Helper script deletes itself
```

### 1. Three-Day Check Cooldown & Release History Cache
- **Cooldown Constant**: `UPDATE_CHECK_INTERVAL_SECONDS = 259200` (3 days) in `speedview/config/config.py`.
- **Persisted State**: `auto_update` (`true` by default) and `last_update_check` (Unix timestamp) live in `network_speed_meter.conf`.
- **All-Version Changelogs**: Live `/releases` payloads are merged with built-in `RELEASE_HISTORY` (`CHANGELOG.md`) and cached in `releases_cache.json`, ensuring **About** and **Updater** dialogs always display features and changelogs across every released version even when offline or after updating.
- **Manual Override**: Clicking **Updates** in Settings or About passes `force=True` to check immediately.

### 2. Platform-Matched Release Asset Selection
| Operating System | Primary `.zip` Asset | Installer / Fallback Assets |
| :--- | :--- | :--- |
| **Windows** (`Windows`) | `*win*.zip` (`SpeedView-windows-x64.zip` `onedir`) | `SpeedView-windows-x64.msi`, `SpeedView-Setup.exe` |
| **macOS** (`Darwin`) | `*mac*` / `*darwin*` / `*osx*.zip` (`SpeedView-macos.zip`) | `.tar.gz`, `.dmg` |
| **Linux** (`Linux`) | `*linux*.zip` (`SpeedView-linux-x64.zip` `onedir`) | `.tar.gz`, `SpeedView-linux-x64-Setup` |

### 3. Detached Python Subprocess Self-Replacement
- `install_update()` spawns `speedview_updater_*.py` using the active Python interpreter (with UAC `ShellExecuteW(..., "runas", ...)` on Windows when updating protected `C:\Program Files\SpeedView`, and native `.bat` / `/bin/sh` fallback on hosts without system Python).
- For `onedir` archives containing both the executable and `_internal/`, `_pick_source_entry()` selects the extracted bundle directory so `shutil.copytree(..., dirs_exist_ok=True)` updates every file inside `Program Files\SpeedView\` cleanly.

---

## Publishing a New Release

1. Update `APP_VERSION` and prepend the new release entry to `RELEASE_HISTORY` in `speedview/config/config.py` (plus `CHANGELOG.md`).
2. Verify everything passes locally:
   ```bash
   python -m compileall -q main.py installer.py speedview tests
   xvfb-run -a python -m unittest discover -s tests -v
   ```
3. Commit your changes, create a version tag, and push:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```
4. GitHub Actions (`.github/workflows/release.yml`) builds and publishes:
   - **Windows**: `SpeedView-windows-x64.msi` (WiX GUI MSI), `SpeedView-Setup.exe` (PyQt5 Setup Wizard), `SpeedView-windows-x64.zip` (`onedir`), `SpeedView-windows-x64.sha256`
   - **macOS**: `SpeedView-macos.zip`, `SpeedView-macos.zip.sha256`
   - **Linux**: `SpeedView-linux-x64.zip`, `SpeedView-linux-x64.tar.gz`, `SpeedView-linux-x64-Setup`, `SpeedView-linux-x64.sha256`

To build locally on Windows, run `scripts\build_windows.bat` or `.\scripts\build_windows.ps1`. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for the pre-release checklist.
