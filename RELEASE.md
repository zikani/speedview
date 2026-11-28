# SpeedView Release & Auto-Updater Guide

This document explains how SpeedView packages cross-platform GitHub Releases and how the built-in background auto-updater downloads, stages, swaps, and restarts updates across Windows, macOS, and Linux.

---

## How the Auto-Updater Works

Because an active desktop application cannot reliably overwrite its own open binary (`SpeedView.exe`, `SpeedView.app`, or `SpeedView-linux-x64`) while running, SpeedView uses a **3-day rate-limited background check + temp `.zip` staging + detached helper swap-and-restart** flow (`speedview/update/updater.py`).

### End-to-End Update Flow

```text
App Startup / 6h Timer
   │
   ▼  (Is auto_update=true AND >= 3 days since last_update_check?)
GitHub Releases API (/releases/latest)
   │
   ▼  (Newer semver tag found? Pick OS-matching .zip asset)
Download .zip ──► Temp Staging Folder (speedview_update_*)
   │
   ▼  (Safe ZipSlip-checked extraction + POSIX chmod preservation)
Launch Detached Helper Script (.bat on Windows / .sh on macOS & Linux)
   │
   ▼
Main App Exits (force_quit)
   │
   ├──► Helper waits for PID exit
   ├──► Replaces old binary or .app bundle from temp folder
   ├──► Removes temporary staging directory
   ├──► Restarts updated SpeedView binary / .app
   └──► Helper script deletes itself
```

### 1. Three-Day Check Cooldown (API Rate-Limit Protection)
- **Cooldown Constant**: `UPDATE_CHECK_INTERVAL_SECONDS = 259200` (3 days) in `speedview/config/config.py`.
- **Persisted State**: `auto_update` (`true` by default) and `last_update_check` (Unix timestamp) are stored in `network_speed_meter.conf`.
- **Non-Blocking Schedule**: `MainWindow` triggers an initial check **2.5 seconds after startup** via `QTimer.singleShot` and polls every **6 hours**, running network requests on a background daemon thread so the UI never freezes.
- **Throttling Rule**: `UpdateChecker.should_check_for_updates(force=False)` skips calling the GitHub API unless at least 3 days have elapsed since `last_update_check`.
- **Manual Override**: Clicking **Updates** in the Settings dialog (or triggering `check_for_updates()`) passes `force=True` to check immediately regardless of the 3-day cooldown.

### 2. Platform-Matched Release Asset Selection
`UpdateChecker.check_for_updates()` queries `DEFAULT_UPDATE_URL` (`https://api.github.com/repos/zikani/speedview/releases/latest`), strips any leading `v` from `tag_name`, and compares it against `APP_VERSION` using `packaging.version`.

When a newer version exists, `_select_asset_for_platform()` prefers the matching `.zip` archive for the host OS (with binary/tarball fallbacks):

| Operating System | Primary `.zip` Asset | Fallback Assets |
| :--- | :--- | :--- |
| **Windows** (`Windows`) | `*win*.zip` (`SpeedView-windows-x64.zip`) | Generic `.zip`, `.exe` |
| **macOS** (`Darwin`) | `*mac*` / `*darwin*` / `*osx*.zip` (`SpeedView-macos.zip`) | `.tar.gz`, `.dmg` |
| **Linux** (`Linux`) | `*linux*.zip` (`SpeedView-linux-x64.zip`) | `.tar.gz`, `.appimage`, `.deb` |

### 3. Temporary Folder Download & Safe Extraction
- `download_update()` streams the archive into a unique temporary staging folder created via `tempfile.mkdtemp(prefix="speedview_update_")`.
- `.zip` archives are extracted into `<staged_dir>/extracted/` using `_safe_extract_zip()`, which validates resolved paths against the extraction root (preventing ZipSlip path traversal) and restores POSIX file permission bits (`chmod`).

### 4. Detached Python Subprocess Self-Replacement
Once an update archive finishes downloading and extracting in the temporary folder:
- **Packaged & Source Support**: `can_self_replace()` returns `True` for packaged binaries (`SpeedView.exe`, `SpeedView.app`, `SpeedView-linux-x64`) using OS binary `.zip` assets as well as local source checkouts (`python main.py`) using GitHub's `zipball_url` source archive (or binary asset fallback).
- **Python Subprocess Helper (`speedview_updater_*.py`)**: Spawns a detached Python subprocess (`subprocess.Popen([sys.executable, helper_script])`) that waits for the parent PID to exit (`os.kill` on macOS/Linux, Win32 `WaitForSingleObject` on Windows), copies/replaces the target binary, `.app` bundle, or source directory cleanly via `shutil`, deletes the temporary staging folder, relaunches the updated app, and removes itself. (If a standalone frozen build runs on a host with no system Python installed, `install_update()` automatically falls back to a detached `.bat` / `/bin/sh` helper.)

### 5. Configuration Controls
Users can configure update behavior in **Settings → Behavior & System Tray** or directly in `network_speed_meter.conf`:
- `auto_update`: Enable or disable automatic 3-day background checks and auto-apply.
- `update_url`: Override the GitHub Releases API endpoint for mirrors or testing.
- `last_update_check`: Timestamp of the most recent check attempt.

---

## Publishing a New Release

Releases are automated via PyInstaller (`.github/workflows/release.yml`) and `speedview.spec`:

1. Bump `APP_VERSION` in `speedview/config/config.py`.
2. Verify everything passes locally:
   ```bash
   python -m compileall -q main.py speedview tests
   xvfb-run -a python -m unittest discover -s tests -v   # Linux headless
   ```
3. Commit your changes, create a version tag, and push:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```
4. GitHub Actions builds and publishes:
   - **Windows**: `SpeedView.exe`, `SpeedView-windows-x64.zip`, `SpeedView-windows-x64.sha256`
   - **macOS**: `SpeedView-macos.zip`, `SpeedView-macos.zip.sha256`
   - **Linux**: `SpeedView-linux-x64`, `SpeedView-linux-x64.tar.gz`, `SpeedView-linux-x64.zip`, `SpeedView-linux-x64.sha256`

To build `dist\SpeedView.exe` locally on Windows without waiting for CI, run `scripts\build_windows.bat` or `.\scripts\build_windows.ps1`. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for the pre-release verification checklist.
