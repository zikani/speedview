# SpeedView Release Checklist

## 1. Pre-Release
- [x] Update version number in `speedview/config/config.py` (`APP_VERSION`) and About dialog
- [x] Ensure `README.md` is up to date (banner/UI showcase SVGs, ping badge, corner float pill, close-to-float lifecycle, `start_on_startup`, PyInstaller release guide)
- [x] Ensure `LICENSE` file is present and correct
- [x] Check `requirements.txt` includes cross-platform environment markers (`pywin32`, `winshell` gated to `win32`) and `pyinstaller`

## 2. Functionality
- [x] Application launches without error on Linux (`Xvfb` / desktop) and guards Windows-only modules (`winreg`, `win32*`, `winshell`)
- [x] Main frameless SVG speedometer displays real-time speed, cogwheel gear settings button, and live ping/latency (`#pingBadge`)
- [x] Real network interface detection reports Ethernet / Wi-Fi / Virtual / Loopback, IPv4/IPv6, link speed, and SSID/band
- [x] System tray integration works (`Show`, `Float Mode`, `Data Usage`, `Settings`, `Test Network`, `Exit`) with synced tooltip
- [x] Modern Settings dialog loads via `findData()`/`itemData()`, validates, saves, restores defaults, and configures OS `start_on_startup`
- [x] Transparent compact corner Float widget (`136x40`) shows signal + speed only and anchors in the bottom-right corner on popup
- [x] Closing Main / Data Usage / Network Test opens Float gadget; closing Float minimizes to tray in background
- [x] Live HTTP test-file speed test streams real-time download & upload metrics (`measure_file_speed`)
- [x] Data Usage SVG window opens and displays `App | Data | Date` for Daily and Monthly views backed by SQLite

## 3. Error Handling
- [x] App handles disconnected network / failed speed test gracefully without UI freezes
- [x] Background GitHub Release updater enforces 3-day cooldown (`last_update_check`), downloads `.zip` to temp dir, and uses detached helper script to swap & restart cleanly
- [x] Dialogs validate input without crashing

## 4. Persistence
- [x] Settings persist across sessions in `network_speed_meter.conf` (including `start_on_startup`)
- [x] Window size, position, `start_minimized`, and `is_floating` are restored on launch
- [x] Daily and monthly traffic data persists in `data_usage.db`

## 5. Testing & CI
- [x] Bytecode check (`python -m compileall -q main.py speedview tests`) passes cleanly
- [x] All unit tests pass (`python -m unittest discover -s tests -v`)
- [x] GitHub Actions CI workflow (`.github/workflows/ci.yml`) configured for Ubuntu and Windows

## 6. Packaging & Release
- [x] Shared `speedview.spec` + Windows build scripts (`scripts/build_windows.bat`, `scripts/build_windows.ps1`) package standalone `dist\SpeedView.exe` and `dist\SpeedView-windows-x64.zip`
- [x] Automated PyInstaller GitHub Action (`.github/workflows/release.yml`) configured for Windows (`SpeedView.exe` / `SpeedView-windows-x64.zip`), macOS (`SpeedView-macos.zip`), and Linux (`SpeedView-linux-x64.zip`/`.tar.gz`/binary) on `v*` tags
- [ ] Push version tag (`git tag vX.Y.Z && git push origin vX.Y.Z`) to publish release binaries and verify live updater check
